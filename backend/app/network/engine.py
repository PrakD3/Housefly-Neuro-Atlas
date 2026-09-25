"""
Network Analysis Engine for Drosophila-NeuroAtlas Phase 6.

Integrates structural, centrality, target-centered, and perturbation dynamic metrics
into a unified, typed analysis result with complete provenance.

SCIENTIFIC PRINCIPLE:
Network metrics describe the analyzed computational graph and should not automatically
be interpreted as measurements of biological importance or causal influence.
All dynamic metrics represent 'modeled activity' within the discrete-time graph simulation.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Union

import networkx as nx

from ..models.connectome import SubgraphResponse
from ..models.network import (
    NetworkAnalysisProvenance,
    NetworkAnalysisRequest,
    NetworkAnalysisResult,
)
from ..models.simulation import SimulationResult
from .centrality import compute_centrality_metrics
from .metrics import compute_structural_metrics
from .paths import compute_target_analysis
from .perturbation import compute_perturbation_analysis

logger = logging.getLogger(__name__)

# Bounded graph safety limits
MAX_ANALYSIS_NODES = 500
MAX_ANALYSIS_EDGES = 5000
MAX_PATH_LENGTH = 10


def _ensure_digraph(
    graph: Union[nx.DiGraph, SubgraphResponse, Dict[str, any]],
) -> nx.DiGraph:
    """Convert supported graph inputs to a directed NetworkX graph with node/edge attributes."""
    if isinstance(graph, nx.DiGraph):
        return graph

    dg = nx.DiGraph()

    if isinstance(graph, SubgraphResponse):
        for n in graph.neurons:
            dg.add_node(
                str(n.neuron_id),
                cell_type=n.cell_type,
                region=n.region,
                x=n.x,
                y=n.y,
                z=n.z,
                has_coordinates=n.has_coordinates,
            )
        for c in graph.connections:
            dg.add_edge(
                str(c.source_neuron),
                str(c.target_neuron),
                weight=float(c.weight),
            )
        return dg

    if isinstance(graph, dict):
        neurons = graph.get("neurons", [])
        connections = graph.get("connections", [])
        for n in neurons:
            if isinstance(n, dict):
                nid = str(n.get("neuron_id"))
                dg.add_node(
                    nid,
                    cell_type=n.get("cell_type", "Unknown"),
                    region=n.get("region", "Unknown"),
                    x=n.get("x"),
                    y=n.get("y"),
                    z=n.get("z"),
                    has_coordinates=n.get("has_coordinates", False),
                )
        for c in connections:
            if isinstance(c, dict):
                dg.add_edge(
                    str(c.get("source_neuron")),
                    str(c.get("target_neuron")),
                    weight=float(c.get("weight", 1.0)),
                )
        return dg

    raise ValueError(f"Unsupported graph type for network analysis: {type(graph)}")


class NetworkAnalysisEngine:
    """
    Dedicated analysis engine executing Phase 6 structural and perturbation dynamic metrics.
    Operates on bounded connectome subgraphs.
    """

    def __init__(self):
        pass

    def analyze(
        self,
        graph: Union[nx.DiGraph, SubgraphResponse, Dict[str, any]],
        simulation_result: SimulationResult,
        threshold: float = 0.05,
        max_hops: int = 3,
    ) -> NetworkAnalysisResult:
        """
        Run complete network analysis combining graph topology and simulation dynamics.

        Parameters:
        - graph: Subgraph (as nx.DiGraph, SubgraphResponse, or dict)
        - simulation_result: Phase 5 SimulationResult containing baseline/perturbed states
        - threshold: Activity delta threshold for model-affected neuron classification
        - max_hops: Reachability hop depth for target-centered analysis

        Raises:
        - ValueError if graph exceeds safety bounds (MAX_ANALYSIS_NODES, MAX_ANALYSIS_EDGES)
        """
        dg = _ensure_digraph(graph)

        n_nodes = dg.number_of_nodes()
        n_edges = dg.number_of_edges()

        if n_nodes > MAX_ANALYSIS_NODES:
            raise ValueError(
                f"Graph size of {n_nodes} nodes exceeds analysis limit ({MAX_ANALYSIS_NODES}). "
                "Please analyze a smaller bounded subgraph."
            )

        if n_edges > MAX_ANALYSIS_EDGES:
            raise ValueError(
                f"Graph connection count of {n_edges} edges exceeds analysis limit ({MAX_ANALYSIS_EDGES})."
            )

        clamped_hops = min(max(1, max_hops), MAX_PATH_LENGTH)
        clamped_thresh = min(max(0.0, threshold), 1.0)

        # 1. Structural metrics
        structural_metrics = compute_structural_metrics(dg)

        # 2. Centrality metrics
        centralities = compute_centrality_metrics(dg)

        # 3. Target-centered reachability analysis
        target_ids = sorted(
            list(
                {
                    target
                    for p in simulation_result.provenance.perturbations
                    for target in p.target_neuron_ids
                }
            )
        )
        target_analysis = compute_target_analysis(
            dg, target_neuron_ids=target_ids, max_hops=clamped_hops
        )

        # 4. Perturbation and propagation dynamic metrics
        perturbation_analysis = compute_perturbation_analysis(
            graph=dg,
            simulation_result=simulation_result,
            threshold=clamped_thresh,
            max_hops=clamped_hops,
        )

        # 5. Provenance tracking
        sim_prov = simulation_result.provenance
        provenance = NetworkAnalysisProvenance(
            simulation_id=simulation_result.simulation_id,
            connectome_provider=sim_prov.connectome_provider,
            dataset_name=sim_prov.dataset_name,
            dataset_version=sim_prov.dataset_version,
            is_synthetic=sim_prov.is_synthetic,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_version="0.1.0-phase6",
            threshold=clamped_thresh,
            max_hops=clamped_hops,
            neuron_count=n_nodes,
            connection_count=n_edges,
        )

        return NetworkAnalysisResult(
            simulation_id=simulation_result.simulation_id,
            network_metrics=structural_metrics,
            centrality=centralities,
            target_analysis=target_analysis,
            perturbation_analysis=perturbation_analysis,
            provenance=provenance,
        )
