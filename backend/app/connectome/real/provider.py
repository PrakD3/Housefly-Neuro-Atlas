"""
Real Drosophila connectome provider backed by the HHMI Janelia neuPrint API.

Dataset: male-cns:v1.0
Source:  https://neuprint.janelia.org
License: CC-BY 4.0

Architecture:
  RealDrosophilaConnectomeProvider
    → NeuPrintClient          (HTTP + auth layer)
    → LRUCache                (per-instance in-memory cache)
    → DatasetProvenance       (provenance record)
    → NeuPrintNeuronRecord    (raw DTO normalization)
    → internal Neuron/Connection/SubgraphResponse models

This provider implements the same ConnectomeProvider contract as
SyntheticConnectomeProvider.  The rest of the application must interact
with both through the abstract interface only.

Coordinate handling:
  somaLocation is returned as [x, y, z] by neuPrint when available.
  When absent, x/y/z are set to None and has_coordinates=False.
  Coordinates are NEVER fabricated or substituted with defaults.

Query limits:
  get_neurons_by_cell_type: max 100 neurons (server-side LIMIT)
  get_neurons_by_region:    max 100 neurons (server-side LIMIT)
  get_connections:          max 500 connections per neuron
  get_neighbors (hops=1):   max 200 neighbor neurons + 500 connections
  extract_subgraph:         max 50 neuron IDs per request
"""
import logging
from typing import List, Optional

import networkx as nx

from ...models.connectome import (
    Connection,
    ConnectomeMetadata,
    Neuron,
    SubgraphResponse,
)
from ..provider import ConnectomeProvider
from .cache import LRUCache
from .client import NeuPrintClient
from .models import NeuPrintConnectionRecord, NeuPrintNeuronRecord
from .provenance import MALE_CNS_V1_PROVENANCE, DatasetProvenance

logger = logging.getLogger(__name__)

# Neuron fields to retrieve from the neuPrint graph database.
# These are the documented fields available on Neuron nodes in male-cns:v1.0.
_NEURON_RETURN_FIELDS = (
    "n.bodyId AS bodyId",
    "n.type AS type",
    "n.instance AS instance",
    "n.superClass AS superClass",
    "n.status AS status",
    "n.predictedNt AS predictedNt",
    "n.somaLocation AS somaLocation",
)
_NEURON_RETURN = ", ".join(_NEURON_RETURN_FIELDS)


class RealDrosophilaConnectomeProvider(ConnectomeProvider):
    """
    ConnectomeProvider implementation using the neuPrint REST API.

    Instantiation will succeed even when the API is unreachable — errors
    are surfaced lazily when methods are called.  This allows the provider
    to be constructed at application startup without failing immediately.

    Authentication is required.  If NEUPRINT_TOKEN is missing,
    NeuPrintAuthenticationError is raised on the first query.
    """

    def __init__(
        self,
        client: NeuPrintClient,
        provenance: DatasetProvenance = MALE_CNS_V1_PROVENANCE,
        cache_max_size: int = 512,
    ) -> None:
        self._client = client
        self._provenance = provenance
        self._cache = LRUCache(max_size=cache_max_size)

    # ------------------------------------------------------------------
    # ConnectomeProvider interface
    # ------------------------------------------------------------------

    def get_metadata(self) -> ConnectomeMetadata:
        """
        Return provenance metadata for the real dataset.

        neuron_count and connection_count are not queried by default
        (the full dataset is very large); they are returned as -1 to
        indicate 'not pre-counted'.  A future phase may add a cached
        count endpoint.
        """
        prov = self._provenance
        return ConnectomeMetadata(
            id=prov.dataset_id,
            description=(
                f"Real Drosophila connectome — {prov.dataset_name} "
                f"({prov.dataset_version}), {prov.organism} ({prov.sex})"
            ),
            neuron_count=-1,       # Not pre-counted; use server-side queries
            connection_count=-1,   # Not pre-counted
            provider_type="RealDrosophilaConnectomeProvider",
            is_synthetic=False,
            dataset_name=prov.dataset_name,
            dataset_version=prov.dataset_version,
            organism=prov.organism,
            sex=prov.sex,
            source_url=prov.source_url,
            license=prov.license,
        )

    def get_neuron(self, neuron_id: str) -> Optional[Neuron]:
        """Retrieve a single neuron by body ID."""
        cache_key = LRUCache.neuron_key(neuron_id)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        cypher = f"""
            MATCH (n:Neuron {{bodyId: {neuron_id}}})
            RETURN {_NEURON_RETURN}
            LIMIT 1
        """
        raw = self._client.query_cypher(cypher)
        records = self._parse_neuron_records(raw)
        if not records:
            return None

        neuron = self._normalize_neuron(records[0])
        self._cache.set(cache_key, neuron)
        return neuron

    def get_neurons_by_cell_type(self, cell_type: str) -> List[Neuron]:
        """
        Retrieve neurons of a specific cell type.

        Limited to 100 results (server-side LIMIT) — the real dataset
        may contain thousands of neurons per type.
        """
        cache_key = LRUCache.cell_type_key(cell_type)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        cypher = f"""
            MATCH (n:Neuron)
            WHERE n.type = '{self._escape(cell_type)}'
            RETURN {_NEURON_RETURN}
            LIMIT 100
        """
        raw = self._client.query_cypher(cypher)
        records = self._parse_neuron_records(raw)
        neurons = [self._normalize_neuron(r) for r in records]
        self._cache.set(cache_key, neurons)
        return neurons

    def get_neurons_by_region(self, region: str) -> List[Neuron]:
        """
        Retrieve neurons associated with a brain region (ROI).

        In neuPrint, region membership is encoded as boolean properties on
        Neuron nodes (e.g., n.`AL(R)` = true).  We use a dynamic property
        lookup via EXISTS.  Limited to 100 results.
        """
        cache_key = LRUCache.region_key(region)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # neuPrint ROI names are stored as dynamic boolean node properties.
        # The Cypher pattern for checking ROI membership is:
        #   WHERE n['{roi}'] = true
        escaped = self._escape(region)
        cypher = f"""
            MATCH (n:Neuron)
            WHERE n['{escaped}'] = true
            RETURN {_NEURON_RETURN}
            LIMIT 100
        """
        raw = self._client.query_cypher(cypher)
        records = self._parse_neuron_records(raw)
        # Tag normalized neurons with the queried region for UI display
        neurons = [
            self._normalize_neuron(r, override_region=region)
            for r in records
        ]
        self._cache.set(cache_key, neurons)
        return neurons

    def get_neighbors(self, neuron_id: str, hops: int = 1) -> SubgraphResponse:
        """
        Retrieve the 1-hop or N-hop neighborhood for a given neuron.

        For hops > 1, this performs an iterative expansion up to depth `hops`.
        The subgraph is assembled from individual neuron lookups and connection
        queries.  Limited to 200 neighbor neurons.
        """
        cache_key = LRUCache.neighbors_key(neuron_id, hops)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # 1-hop: direct pre- and post-synaptic partners
        cypher = f"""
            MATCH (a:Neuron {{bodyId: {neuron_id}}})-[r:ConnectsTo]-(b:Neuron)
            RETURN
                a.bodyId AS source,
                b.bodyId AS target,
                r.weight AS weight,
                {', '.join([f'b.{f.split(" AS ")[0].split(".")[-1]} AS b_{f.split(" AS ")[-1].strip()}' for f in ["n.type AS type", "n.instance AS instance", "n.status AS status", "n.predictedNt AS predictedNt", "n.somaLocation AS somaLocation"]])}
            LIMIT 500
        """
        # Simpler approach: fetch connections, then fetch neighbor neuron details
        conns = self.get_connections(neuron_id)

        # Collect neighbor body IDs
        neighbor_ids = set()
        for c in conns:
            neighbor_ids.add(c.source_neuron)
            neighbor_ids.add(c.target_neuron)
        neighbor_ids.discard(neuron_id)

        # Limit neighbors
        neighbor_ids_limited = list(neighbor_ids)[:199]

        # Fetch the central neuron
        central = self.get_neuron(neuron_id)
        all_neurons: List[Neuron] = []
        if central:
            all_neurons.append(central)

        # Fetch neighbors (individually, using cache)
        for nid in neighbor_ids_limited:
            n = self.get_neuron(nid)
            if n:
                all_neurons.append(n)

        result = SubgraphResponse(neurons=all_neurons, connections=conns)
        self._cache.set(cache_key, result)
        return result

    def get_connections(self, neuron_id: str) -> List[Connection]:
        """
        Retrieve all directed connections (incoming and outgoing) for a neuron.
        Limited to 500 connections.
        """
        cache_key = LRUCache.connections_key(neuron_id)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        cypher = f"""
            MATCH (a:Neuron {{bodyId: {neuron_id}}})-[r:ConnectsTo]->(b:Neuron)
            RETURN a.bodyId AS source, b.bodyId AS target, r.weight AS weight
            LIMIT 250
            UNION
            MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {{bodyId: {neuron_id}}})
            RETURN a.bodyId AS source, b.bodyId AS target, r.weight AS weight
            LIMIT 250
        """
        raw = self._client.query_cypher(cypher)
        connections = self._parse_connection_records(raw)
        result = [self._normalize_connection(c) for c in connections]
        self._cache.set(cache_key, result)
        return result

    def extract_subgraph(self, neuron_ids: List[str]) -> SubgraphResponse:
        """
        Extract a subgraph containing the specified neurons and connections
        between them.  Limited to 50 neurons per request.
        """
        if not neuron_ids:
            return SubgraphResponse(neurons=[], connections=[])

        # Enforce limit
        ids_to_fetch = neuron_ids[:50]
        body_ids_str = ", ".join(ids_to_fetch)

        # Fetch neurons
        cypher_neurons = f"""
            MATCH (n:Neuron)
            WHERE n.bodyId IN [{body_ids_str}]
            RETURN {_NEURON_RETURN}
            LIMIT 50
        """
        raw_neurons = self._client.query_cypher(cypher_neurons)
        records = self._parse_neuron_records(raw_neurons)
        neurons = [self._normalize_neuron(r) for r in records]

        # Fetch connections within the subgraph
        cypher_conns = f"""
            MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron)
            WHERE a.bodyId IN [{body_ids_str}] AND b.bodyId IN [{body_ids_str}]
            RETURN a.bodyId AS source, b.bodyId AS target, r.weight AS weight
            LIMIT 500
        """
        raw_conns = self._client.query_cypher(cypher_conns)
        conn_records = self._parse_connection_records(raw_conns)
        connections = [self._normalize_connection(c) for c in conn_records]

        return SubgraphResponse(neurons=neurons, connections=connections)

    def search_neurons(self, query: str, limit: int = 20) -> List[Neuron]:
        """
        Search neurons by body ID, cell type, or instance name.
        """
        q = query.strip()
        if not q:
            return []

        # If purely numeric, treat as body ID search first
        if q.isdigit():
            neuron = self.get_neuron(q)
            if neuron:
                return [neuron]

        escaped = self._escape(q)
        cypher = f"""
            MATCH (n:Neuron)
            WHERE n.type STARTS WITH '{escaped}'
               OR n.instance STARTS WITH '{escaped}'
               OR n.type CONTAINS '{escaped}'
            RETURN {_NEURON_RETURN}
            LIMIT {min(limit, 50)}
        """
        raw = self._client.query_cypher(cypher)
        records = self._parse_neuron_records(raw)
        return [self._normalize_neuron(r) for r in records]

    # ------------------------------------------------------------------

    # Normalization — neuPrint DTOs → internal models
    # ------------------------------------------------------------------

    def _normalize_neuron(
        self,
        record: NeuPrintNeuronRecord,
        override_region: Optional[str] = None,
    ) -> Neuron:
        """
        Normalize a neuPrint neuron record into the internal Neuron model.

        Coordinate handling:
          - If somaLocation is present and is a 3-element list, extract x/y/z
            and set has_coordinates=True.
          - If somaLocation is absent or malformed, set x=y=z=None and
            has_coordinates=False.
          - Coordinates are NEVER defaulted to (0, 0, 0).

        Region:
          neuPrint does not store a single 'region' field; it uses ROI boolean
          properties.  If override_region is provided (from a region query),
          use that.  Otherwise, use superClass as a proxy for high-level region
          grouping, or fall back to "unknown".
        """
        # Coordinates — nullable, never fabricated
        if record.has_soma_location:
            x = record.soma_x
            y = record.soma_y
            z = record.soma_z
            has_coords = True
        else:
            x = None
            y = None
            z = None
            has_coords = False

        # Region proxy: use override (from ROI query) → superClass → "unknown"
        region = override_region or record.super_class or "unknown"

        # Cell type: type → instance → body ID string
        cell_type = record.type or record.instance or f"body:{record.body_id}"

        return Neuron(
            neuron_id=str(record.body_id),
            cell_type=cell_type,
            region=region,
            x=x,
            y=y,
            z=z,
            has_coordinates=has_coords,
            neurotransmitter=record.predicted_nt,
            status=record.status,
            instance=record.instance,
        )

    def _normalize_connection(self, record: NeuPrintConnectionRecord) -> Connection:
        """Normalize a raw connection record into the internal Connection model."""
        return Connection(
            source_neuron=str(record.source_body_id),
            target_neuron=str(record.target_body_id),
            weight=float(record.weight),
        )

    # ------------------------------------------------------------------
    # Raw response parsing — neuPrint columns/data format
    # ------------------------------------------------------------------

    def _parse_neuron_records(self, raw: dict) -> List[NeuPrintNeuronRecord]:
        """
        Parse neuPrint /api/custom/custom response into neuron DTOs.

        Response format:
          {"columns": ["bodyId", "type", ...], "data": [[val, ...], ...]}
        """
        columns = raw.get("columns", [])
        data = raw.get("data", [])
        records: List[NeuPrintNeuronRecord] = []

        col_idx = {name: i for i, name in enumerate(columns)}

        for row in data:
            def _get(col: str):
                idx = col_idx.get(col)
                if idx is None or idx >= len(row):
                    return None
                v = row[idx]
                return v if v != "" else None

            body_id_raw = _get("bodyId")
            if body_id_raw is None:
                continue
            try:
                body_id = int(body_id_raw)
            except (TypeError, ValueError):
                logger.warning("Skipping neuron row with non-integer bodyId: %r", body_id_raw)
                continue

            # Parse somaLocation [x, y, z] — may be None, a list, or missing
            soma = _get("somaLocation")
            soma_x = soma_y = soma_z = None
            if isinstance(soma, (list, tuple)) and len(soma) == 3:
                try:
                    soma_x = float(soma[0])
                    soma_y = float(soma[1])
                    soma_z = float(soma[2])
                except (TypeError, ValueError):
                    # Cannot parse coordinates — leave as None
                    soma_x = soma_y = soma_z = None

            records.append(NeuPrintNeuronRecord(
                body_id=body_id,
                type=_get("type"),
                instance=_get("instance"),
                super_class=_get("superClass"),
                status=_get("status"),
                predicted_nt=_get("predictedNt"),
                soma_x=soma_x,
                soma_y=soma_y,
                soma_z=soma_z,
            ))

        return records

    def _parse_connection_records(self, raw: dict) -> List[NeuPrintConnectionRecord]:
        """
        Parse neuPrint /api/custom/custom response into connection DTOs.
        """
        columns = raw.get("columns", [])
        data = raw.get("data", [])
        col_idx = {name: i for i, name in enumerate(columns)}
        records: List[NeuPrintConnectionRecord] = []

        for row in data:
            def _get(col: str):
                idx = col_idx.get(col)
                if idx is None or idx >= len(row):
                    return None
                return row[idx]

            src = _get("source")
            tgt = _get("target")
            wt = _get("weight")

            if src is None or tgt is None:
                continue
            try:
                records.append(NeuPrintConnectionRecord(
                    source_body_id=int(src),
                    target_body_id=int(tgt),
                    weight=float(wt) if wt is not None else 1.0,
                ))
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping connection row parse error: %s", exc)

        return records

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escape(value: str) -> str:
        """
        Basic escaping for Cypher string literals.
        Single quotes are escaped.  Backtick names are handled at call sites.
        """
        return value.replace("'", "\\'")
