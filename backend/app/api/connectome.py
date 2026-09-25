"""
Connectome API routes.

All routes are provider-agnostic: they call get_provider() and work
identically regardless of whether the active provider is synthetic or real.

Error handling:
  NeuPrintAuthenticationError  → HTTP 503  (real connectome unavailable)
  NeuPrintConnectionError      → HTTP 503  (real connectome unavailable)
  NeuPrintDatasetError         → HTTP 503  (real connectome unavailable)
  NeuPrintError (base)         → HTTP 503  (real connectome unavailable)
  NeuronNotFound               → HTTP 404
  Unexpected exception         → HTTP 500 (logged server-side)

The synthetic provider does not raise any of the neuPrint exceptions, so
existing synthetic-mode behavior is fully preserved.
"""
from datetime import datetime, timezone
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.connectome import (
    BoundedSubgraphResponse,
    Connection,
    ConnectomeMetadata,
    Neuron,
    SubgraphProvenance,
    SubgraphResponse,
)
from ..connectome.factory import get_provider
from ..connectome.real.client import (
    NeuPrintAuthenticationError,
    NeuPrintConnectionError,
    NeuPrintDatasetError,
    NeuPrintError,
    NeuPrintRateLimitError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectome", tags=["connectome"])

# Default limit for listing neurons when no filter is applied.
# The real connectome is too large to list without a filter.
_DEFAULT_NEURON_LIST_LIMIT = 50


def _provider_unavailable(exc: Exception) -> HTTPException:
    """Map a neuPrint error to a structured HTTP 503 response."""
    if isinstance(exc, NeuPrintAuthenticationError):
        detail = (
            "Real connectome unavailable — authentication required. "
            "Set NEUPRINT_TOKEN in your environment."
        )
    elif isinstance(exc, NeuPrintRateLimitError):
        detail = "Real connectome temporarily unavailable — rate limit exceeded. Please retry."
    elif isinstance(exc, NeuPrintDatasetError):
        detail = "Real connectome unavailable — dataset not found. Check NEUPRINT_DATASET."
    elif isinstance(exc, NeuPrintConnectionError):
        detail = "Real connectome unavailable — could not reach neuPrint server."
    else:
        detail = "Real connectome unavailable — unexpected error. Check server logs."
    return HTTPException(status_code=503, detail=detail)


@router.get("/info", response_model=ConnectomeMetadata)
def get_connectome_info():
    """Retrieve metadata about the currently loaded connectome."""
    try:
        return get_provider().get_metadata()
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/info: %s", exc)
        raise _provider_unavailable(exc)


@router.get("/neurons", response_model=List[Neuron])
def get_neurons(
    cell_type: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(_DEFAULT_NEURON_LIST_LIMIT, ge=1, le=500),
):
    """
    Retrieve neurons, optionally filtered by cell_type or region.

    For the real connectome, results are capped by the provider at 100
    per query.  For synthetic data, all neurons are returned unless filtered.
    """
    try:
        provider = get_provider()

        if cell_type and region:
            neurons_by_type = {n.neuron_id: n for n in provider.get_neurons_by_cell_type(cell_type)}
            neurons_by_region = {n.neuron_id: n for n in provider.get_neurons_by_region(region)}
            common_ids = set(neurons_by_type.keys()) & set(neurons_by_region.keys())
            return [neurons_by_type[nid] for nid in list(common_ids)[:limit]]
        elif cell_type:
            return provider.get_neurons_by_cell_type(cell_type)[:limit]
        elif region:
            return provider.get_neurons_by_region(region)[:limit]
        else:
            # No filter: for synthetic, return all; for real, refuse without filter
            meta = provider.get_metadata()
            if meta.is_synthetic:
                # Synthetic: return all via neurons_metadata (existing behaviour)
                from ..connectome.synthetic import SyntheticConnectomeProvider
                if isinstance(provider, SyntheticConnectomeProvider):
                    return list(provider.neurons_metadata.values())[:limit]
            # Real provider without filter — require at least one filter
            raise HTTPException(
                status_code=400,
                detail=(
                    "The real connectome is too large to list without a filter. "
                    "Provide cell_type or region query parameters."
                ),
            )
    except HTTPException:
        raise
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/neurons: %s", exc)
        raise _provider_unavailable(exc)


@router.get("/neurons/{neuron_id}", response_model=Neuron)
def get_neuron(neuron_id: str):
    """Retrieve a single neuron by ID."""
    try:
        neuron = get_provider().get_neuron(neuron_id)
        if not neuron:
            raise HTTPException(status_code=404, detail=f"Neuron '{neuron_id}' not found")
        return neuron
    except HTTPException:
        raise
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/neurons/%s: %s", neuron_id, exc)
        raise _provider_unavailable(exc)


@router.get("/neurons/{neuron_id}/neighbors", response_model=SubgraphResponse)
def get_neuron_neighbors(neuron_id: str, hops: int = Query(1, ge=1, le=3)):
    """
    Retrieve the neighborhood subgraph for a given neuron up to `hops` distance.

    Maximum hops is limited to 3 for the real connectome due to the
    potentially very large expansion size.
    """
    try:
        provider = get_provider()
        neuron = provider.get_neuron(neuron_id)
        if not neuron:
            raise HTTPException(status_code=404, detail=f"Neuron '{neuron_id}' not found")
        return provider.get_neighbors(neuron_id, hops)
    except HTTPException:
        raise
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/neurons/%s/neighbors: %s", neuron_id, exc)
        raise _provider_unavailable(exc)


@router.post("/subgraph", response_model=SubgraphResponse)
def extract_subgraph(neuron_ids: List[str]):
    """
    Extract a subgraph containing the specified neurons and any edges between them.

    For the real connectome, limited to 50 neuron IDs per request.
    """
    if not neuron_ids:
        return SubgraphResponse(neurons=[], connections=[])
    try:
        return get_provider().extract_subgraph(neuron_ids)
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/subgraph: %s", exc)
        raise _provider_unavailable(exc)


# Hard safety limits for bounded visualization subgraphs
MAX_SUBGRAPH_NEURONS = 500
MAX_SUBGRAPH_CONNECTIONS = 2000


@router.get("/neighborhood", response_model=BoundedSubgraphResponse)
def get_neighborhood(
    neuron_id: str,
    hops: int = Query(1, ge=1, le=2),
    max_neurons: int = Query(MAX_SUBGRAPH_NEURONS, ge=1, le=MAX_SUBGRAPH_NEURONS),
    max_connections: int = Query(MAX_SUBGRAPH_CONNECTIONS, ge=1, le=MAX_SUBGRAPH_CONNECTIONS),
):
    """
    Retrieve a bounded neighborhood subgraph for a given neuron up to `hops` distance.
    Enforces server-side hard limits to protect frontend rendering performance.
    """
    try:
        provider = get_provider()
        central = provider.get_neuron(neuron_id)
        if not central:
            raise HTTPException(status_code=404, detail=f"Neuron '{neuron_id}' not found")

        raw_subgraph = provider.get_neighbors(neuron_id, hops=hops)

        # Retain central neuron + neighbors up to max_neurons
        neurons: List[Neuron] = []
        seen_ids = set()

        neurons.append(central)
        seen_ids.add(central.neuron_id)

        for n in raw_subgraph.neurons:
            if n.neuron_id not in seen_ids:
                if len(neurons) >= max_neurons:
                    break
                neurons.append(n)
                seen_ids.add(n.neuron_id)

        # Retain connections between the kept neurons up to max_connections
        valid_connections = [
            c for c in raw_subgraph.connections
            if c.source_neuron in seen_ids and c.target_neuron in seen_ids
        ]
        connections = valid_connections[:max_connections]

        raw_neuron_ids = {n.neuron_id for n in raw_subgraph.neurons} | {central.neuron_id}
        was_truncated = (
            len(raw_neuron_ids) > max_neurons
            or len(raw_subgraph.connections) > max_connections
            or len(valid_connections) > max_connections
        )

        meta = provider.get_metadata()
        provenance = SubgraphProvenance(
            dataset_name=meta.dataset_name,
            dataset_version=meta.dataset_version,
            is_synthetic=meta.is_synthetic,
            query_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return BoundedSubgraphResponse(
            neurons=neurons,
            connections=connections,
            neuron_count=len(neurons),
            connection_count=len(connections),
            was_truncated=was_truncated,
            max_neurons_limit=max_neurons,
            max_connections_limit=max_connections,
            query_neuron_id=neuron_id,
            hops=hops,
            provenance=provenance,
        )
    except HTTPException:
        raise
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/neighborhood: %s", exc)
        raise _provider_unavailable(exc)


@router.get("/search", response_model=List[Neuron])
def search_neurons(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search neurons by query text (body ID, cell type, instance, or region).
    """
    try:
        provider = get_provider()
        return provider.search_neurons(query, limit=limit)
    except NeuPrintError as exc:
        logger.error("neuPrint error in /connectome/search: %s", exc)
        raise _provider_unavailable(exc)

