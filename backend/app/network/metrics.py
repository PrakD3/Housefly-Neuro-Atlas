"""
Structural Network Metrics for Drosophila-NeuroAtlas Phase 6.

Calculates graph-theoretic properties directly from the connectome graph.
Strictly directed graph definitions are maintained unless explicitly noted.

SCIENTIFIC PRINCIPLE:
Structural metrics describe the topology of the computational graph. They do NOT
indicate biological importance, toxicity, or physiological relevance.
"""
import logging
from typing import Optional

import networkx as nx

from ..models.network import GraphStructuralMetrics

logger = logging.getLogger(__name__)


def compute_structural_metrics(graph: nx.DiGraph) -> GraphStructuralMetrics:
    """
    Compute structural metrics directly from a directed connectome subgraph.

    Handles edge cases gracefully:
    - Empty graph (0 nodes)
    - Single-node graph (1 node)
    - Disconnected graph (multiple weakly connected components)
    - Graph with 0 edges

    Average shortest path length calculation note:
    - For directed graphs, shortest paths are directed u -> v.
    - If graph is strongly connected with >= 2 nodes, directed average shortest path is computed.
    - If not strongly connected, average shortest path is computed over all ordered pairs (u, v)
      where a directed path exists. If no pairs with paths exist, returns None.
    """
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()

    if n_nodes == 0:
        return GraphStructuralMetrics(
            neuron_count=0,
            connection_count=0,
            density=0.0,
            mean_in_degree=0.0,
            mean_out_degree=0.0,
            max_in_degree=0,
            max_out_degree=0,
            strongly_connected_components=0,
            weakly_connected_components=0,
            largest_wcc_size=0,
            average_shortest_path_length=None,
            is_directed=True,
            is_dag=False,
        )

    # In-degrees and Out-degrees
    in_degrees = [d for _, d in graph.in_degree()]
    out_degrees = [d for _, d in graph.out_degree()]

    mean_in = float(sum(in_degrees)) / n_nodes
    mean_out = float(sum(out_degrees)) / n_nodes
    max_in = max(in_degrees) if in_degrees else 0
    max_out = max(out_degrees) if out_degrees else 0

    # Density: for directed graph with n nodes, max edges = n * (n - 1)
    if n_nodes < 2:
        density = 0.0
    else:
        density = float(n_edges) / (n_nodes * (n_nodes - 1))
        density = min(max(density, 0.0), 1.0)

    # Connected components
    scc_count = nx.number_strongly_connected_components(graph)
    wcc_list = list(nx.weakly_connected_components(graph))
    wcc_count = len(wcc_list)
    largest_wcc_size = max(len(c) for c in wcc_list) if wcc_list else 0

    # DAG check
    try:
        is_dag = nx.is_directed_acyclic_graph(graph)
    except Exception:
        is_dag = False

    # Average shortest path length
    avg_spl: Optional[float] = None
    if n_nodes >= 2 and n_edges > 0:
        if nx.is_strongly_connected(graph):
            try:
                avg_spl = round(float(nx.average_shortest_path_length(graph)), 4)
            except Exception as exc:
                logger.debug("Failed strongly connected average shortest path: %s", exc)
                avg_spl = None
        else:
            # Average over all directed pairs (u, v) where path exists
            try:
                total_length = 0
                path_count = 0
                for source in graph.nodes:
                    lengths = nx.single_source_shortest_path_length(graph, source)
                    for target, dist in lengths.items():
                        if source != target:
                            total_length += dist
                            path_count += 1
                if path_count > 0:
                    avg_spl = round(float(total_length) / path_count, 4)
            except Exception as exc:
                logger.debug("Failed path pair average shortest path: %s", exc)
                avg_spl = None

    return GraphStructuralMetrics(
        neuron_count=n_nodes,
        connection_count=n_edges,
        density=round(density, 6),
        mean_in_degree=round(mean_in, 4),
        mean_out_degree=round(mean_out, 4),
        max_in_degree=max_in,
        max_out_degree=max_out,
        strongly_connected_components=scc_count,
        weakly_connected_components=wcc_count,
        largest_wcc_size=largest_wcc_size,
        average_shortest_path_length=avg_spl,
        is_directed=True,
        is_dag=is_dag,
    )
