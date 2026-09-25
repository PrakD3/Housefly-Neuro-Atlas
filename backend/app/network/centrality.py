"""
Centrality Analysis for Drosophila-NeuroAtlas Phase 6.

Calculates standard directed graph centrality metrics:
- In-degree centrality
- Out-degree centrality
- Betweenness centrality (directed)
- Closeness centrality (directed)

SCIENTIFIC PRINCIPLE:
Centrality measures quantify topological positioning within the analyzed subgraph.
They do NOT denote biological importance, neurobiological criticality, or toxicological vulnerability.
Use terminology: 'high modeled network centrality', NOT 'important neuron'.
"""
import logging
from typing import List

import networkx as nx

from ..models.network import CentralityMetricValue

logger = logging.getLogger(__name__)


def compute_centrality_metrics(graph: nx.DiGraph) -> List[CentralityMetricValue]:
    """
    Compute in-degree, out-degree, betweenness, and closeness centrality for all neurons.

    All metrics are calculated on the directed graph without altering edge orientations.
    Safe against empty graphs, 1-node graphs, and disconnected graphs.
    """
    if graph.number_of_nodes() == 0:
        return []

    if graph.number_of_nodes() == 1:
        single_node = next(iter(graph.nodes))
        return [
            CentralityMetricValue(
                neuron_id=str(single_node),
                in_degree_centrality=0.0,
                out_degree_centrality=0.0,
                betweenness_centrality=0.0,
                closeness_centrality=0.0,
            )
        ]

    # Calculate centralities using NetworkX directed formulations
    in_deg_cent = nx.in_degree_centrality(graph)
    out_deg_cent = nx.out_degree_centrality(graph)

    try:
        betw_cent = nx.betweenness_centrality(graph, normalized=True, weight=None)
    except Exception as exc:
        logger.warning("Betweenness centrality calculation failed: %s", exc)
        betw_cent = {n: 0.0 for n in graph.nodes}

    try:
        close_cent = nx.closeness_centrality(graph)
    except Exception as exc:
        logger.warning("Closeness centrality calculation failed: %s", exc)
        close_cent = {n: 0.0 for n in graph.nodes}

    results: List[CentralityMetricValue] = []
    for node in graph.nodes:
        results.append(
            CentralityMetricValue(
                neuron_id=str(node),
                in_degree_centrality=round(float(in_deg_cent.get(node, 0.0)), 4),
                out_degree_centrality=round(float(out_deg_cent.get(node, 0.0)), 4),
                betweenness_centrality=round(float(betw_cent.get(node, 0.0)), 4),
                closeness_centrality=round(float(close_cent.get(node, 0.0)), 4),
            )
        )

    # Sort deterministically by betweenness centrality descending, then node id
    results.sort(key=lambda c: (c.betweenness_centrality, c.in_degree_centrality + c.out_degree_centrality), reverse=True)
    return results
