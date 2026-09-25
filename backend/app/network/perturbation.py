"""
Perturbation and Dynamic Propagation Analysis for Drosophila-NeuroAtlas Phase 6.

Quantifies activity deltas, model-affected neuron classifications,
and network-level perturbation metrics.

SCIENTIFIC PRINCIPLE:
Neurons classified as 'model-affected' are those whose activity delta in the
computational simulation exceeds the specified numerical threshold.
This is a mathematical filter on the model state, NOT a biological toxicity marker.
"""
from typing import Dict, List, Set

import networkx as nx

from ..models.network import (
    ModelAffectedNeuron,
    PerturbationAnalysis,
    PerturbationSummaryMetrics,
)
from ..models.simulation import SimulationResult
from .temporal import compute_temporal_metrics


def compute_perturbation_analysis(
    graph: nx.DiGraph,
    simulation_result: SimulationResult,
    threshold: float = 0.05,
    max_hops: int = 3,
) -> PerturbationAnalysis:
    """
    Compute comprehensive perturbation and propagation metrics from simulation results.

    - Computes delta activity (perturbed - baseline) and absolute delta for each neuron.
    - Classifies neurons as 'model-affected' if absolute delta >= threshold.
    - Computes global network summary metrics (total and mean activity shifts).
    - Preserves target-specific shifts.
    - Calculates temporal trajectories if time-series data is available.
    """
    target_ids: Set[str] = {
        target
        for p in simulation_result.provenance.perturbations
        for target in p.target_neuron_ids
    }

    # Map delta metadata from simulation_result.neuron_deltas
    delta_map = {d.neuron_id: d for d in simulation_result.neuron_deltas}

    # All nodes: union of graph nodes, deltas, and final states
    all_nodes = set(graph.nodes) if graph.number_of_nodes() > 0 else set(delta_map.keys())
    if not all_nodes:
        all_nodes = set(simulation_result.final_state.neuron_activity.keys())

    affected_neurons: List[ModelAffectedNeuron] = []
    base_acts: List[float] = []
    pert_acts: List[float] = []
    abs_deltas: List[float] = []

    for node in sorted(all_nodes):
        d_record = delta_map.get(node)
        node_attrs = graph.nodes[node] if node in graph else {}

        cell_type = (
            d_record.cell_type
            if d_record
            else node_attrs.get("cell_type", "Unknown")
        )
        region = (
            d_record.region
            if d_record
            else node_attrs.get("region", "Unknown")
        )
        has_coords = (
            d_record.has_coordinates
            if d_record
            else node_attrs.get("has_coordinates", False)
        )
        x = d_record.x if d_record else node_attrs.get("x")
        y = d_record.y if d_record else node_attrs.get("y")
        z = d_record.z if d_record else node_attrs.get("z")
        hop_dist = d_record.hop_distance if d_record else None

        base_a = (
            d_record.baseline_activity
            if d_record
            else simulation_result.baseline_final_state.neuron_activity.get(node, 0.0)
        )
        pert_a = (
            d_record.perturbed_activity
            if d_record
            else simulation_result.final_state.neuron_activity.get(node, 0.0)
        )

        delta = round(pert_a - base_a, 4)
        abs_d = round(abs(delta), 4)
        is_target = node in target_ids
        exceeds_thresh = abs_d >= threshold

        base_acts.append(base_a)
        pert_acts.append(pert_a)
        abs_deltas.append(abs_d)

        affected_neurons.append(
            ModelAffectedNeuron(
                neuron_id=str(node),
                cell_type=cell_type,
                region=region,
                baseline_activity=round(base_a, 4),
                perturbed_activity=round(pert_a, 4),
                delta_activity=delta,
                absolute_delta=abs_d,
                hop_distance=hop_dist,
                is_target=is_target,
                exceeds_threshold=exceeds_thresh,
                has_coordinates=has_coords,
                x=x,
                y=y,
                z=z,
            )
        )

    # Sort affected neurons deterministically: model-affected first (by abs delta desc), then node ID
    affected_neurons.sort(
        key=lambda n: (n.exceeds_threshold, n.absolute_delta),
        reverse=True,
    )

    n_count = len(all_nodes)
    total_base = sum(base_acts)
    total_pert = sum(pert_acts)
    delta_total = total_pert - total_base
    mean_base = total_base / n_count if n_count > 0 else 0.0
    mean_pert = total_pert / n_count if n_count > 0 else 0.0
    mean_abs_delta = sum(abs_deltas) / n_count if n_count > 0 else 0.0
    max_abs_delta = max(abs_deltas) if abs_deltas else 0.0

    model_affected_count = sum(1 for n in affected_neurons if n.exceeds_threshold)
    model_affected_frac = float(model_affected_count) / n_count if n_count > 0 else 0.0

    # Per-target activity summary
    target_summary: Dict[str, Dict[str, float]] = {}
    for tid in target_ids:
        tid_str = str(tid)
        t_base = simulation_result.baseline_final_state.neuron_activity.get(tid_str, 0.0)
        t_pert = simulation_result.final_state.neuron_activity.get(tid_str, 0.0)
        target_summary[tid_str] = {
            "baseline": round(t_base, 4),
            "perturbed": round(t_pert, 4),
            "delta": round(t_pert - t_base, 4),
        }

    summary = PerturbationSummaryMetrics(
        threshold=threshold,
        total_baseline_activity=round(total_base, 4),
        total_perturbed_activity=round(total_pert, 4),
        delta_total_activity=round(delta_total, 4),
        mean_baseline_activity=round(mean_base, 4),
        mean_perturbed_activity=round(mean_pert, 4),
        mean_absolute_activity_change=round(mean_abs_delta, 4),
        max_absolute_activity_change=round(max_abs_delta, 4),
        model_affected_neuron_count=model_affected_count,
        model_affected_neuron_fraction=round(model_affected_frac, 4),
        target_activity_summary=target_summary,
    )

    # Compute temporal time-series analysis
    temporal_summary = compute_temporal_metrics(
        time_series=simulation_result.time_series,
        baseline_time_series=simulation_result.baseline_time_series,
        threshold=threshold,
    )

    return PerturbationAnalysis(
        target_neuron_ids=sorted(list(target_ids)),
        threshold=threshold,
        affected_neurons=affected_neurons,
        network_summary=summary,
        temporal_summary=temporal_summary if temporal_summary else None,
    )
