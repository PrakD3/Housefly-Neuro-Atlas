"""
Path and Reachability Analysis for Drosophila-NeuroAtlas Phase 6.

Calculates target-centered reachability, upstream/downstream partners,
and shortest path lengths on directed connectome subgraphs.

SCIENTIFIC PRINCIPLE:
Downstream reachability indicates mathematical path existence within the computational
subgraph. It does not establish biological transmission or functional causality.
"""
from typing import Dict, List, Set

import networkx as nx

from ..models.network import TargetAnalysis


def compute_target_analysis(
    graph: nx.DiGraph,
    target_neuron_ids: List[str],
    max_hops: int = 3,
) -> List[TargetAnalysis]:
    """
    Compute target-centered structural reachability and degree metrics for specified targets.

    For each target:
    - upstream pre-synaptic partners (predecessors in DiGraph)
    - downstream post-synaptic partners (successors in DiGraph)
    - multi-hop downstream reachability layers (1-hop, 2-hop, ..., max_hops)
    - shortest directed path lengths from target to reachable neurons

    Directionality is strictly preserved:
    Target -> 1-hop downstream -> 2-hop downstream -> ...
    """
    results: List[TargetAnalysis] = []

    for target in target_neuron_ids:
        if target not in graph:
            # Target might not exist in this subgraph
            results.append(
                TargetAnalysis(
                    target_neuron_id=target,
                    in_degree=0,
                    out_degree=0,
                    total_degree=0,
                    upstream_neuron_count=0,
                    downstream_neuron_count=0,
                    upstream_neurons=[],
                    downstream_neurons=[],
                    reachability_by_hop={h: [] for h in range(1, max_hops + 1)},
                    reachability_counts={h: 0 for h in range(1, max_hops + 1)},
                    shortest_path_lengths_downstream={},
                )
            )
            continue

        in_deg = graph.in_degree(target)
        out_deg = graph.out_degree(target)
        upstream = sorted(list(graph.predecessors(target)))
        downstream = sorted(list(graph.successors(target)))

        # Multi-hop reachability using directed BFS cutoff
        reachability_by_hop: Dict[int, List[str]] = {h: [] for h in range(1, max_hops + 1)}
        shortest_paths: Dict[str, int] = {}

        try:
            path_lengths = nx.single_source_shortest_path_length(graph, target, cutoff=max_hops)
            for node, dist in path_lengths.items():
                if node == target:
                    continue
                shortest_paths[node] = dist
                if dist in reachability_by_hop:
                    reachability_by_hop[dist].append(node)
        except Exception:
            pass

        # Sort node lists for deterministic output
        for h in reachability_by_hop:
            reachability_by_hop[h].sort()

        reachability_counts = {h: len(reachability_by_hop[h]) for h in range(1, max_hops + 1)}

        results.append(
            TargetAnalysis(
                target_neuron_id=target,
                in_degree=in_deg,
                out_degree=out_deg,
                total_degree=in_deg + out_deg,
                upstream_neuron_count=len(upstream),
                downstream_neuron_count=len(downstream),
                upstream_neurons=upstream,
                downstream_neurons=downstream,
                reachability_by_hop=reachability_by_hop,
                reachability_counts=reachability_counts,
                shortest_path_lengths_downstream=shortest_paths,
            )
        )

    return results
