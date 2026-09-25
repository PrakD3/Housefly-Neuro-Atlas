"""
Temporal Network Analysis for Drosophila-NeuroAtlas Phase 6.

Calculates dynamic time-series metrics from Phase 5 simulation histories.

SCIENTIFIC PRINCIPLE:
Dynamic metrics reflect state trajectories within the discrete-time graph simulation.
They do NOT denote physiological firing frequencies, EPSPs, or in vivo electrophysiology.
Use the term 'modeled activity' throughout.
"""
from typing import Dict, List, Optional

from ..models.network import TemporalNeuronMetrics
from ..models.simulation import SimulationState


def compute_temporal_metrics(
    time_series: List[SimulationState],
    baseline_time_series: List[SimulationState],
    threshold: float = 0.05,
) -> List[TemporalNeuronMetrics]:
    """
    Calculate dynamic time-series metrics for each neuron across the simulation run.

    Metrics:
    - initial_activity: Modeled activity at t = 0
    - final_activity: Modeled activity at simulation termination
    - max_activity: Peak modeled activity over the duration
    - min_activity: Nadir modeled activity over the duration
    - peak_absolute_change: Maximum |perturbed(t) - baseline(t)|
    - time_of_peak_change: Simulation timestamp where peak change occurred
    - area_under_curve: Numerical integration (trapezoidal rule) of modeled activity over time
    - time_to_threshold: First timestamp where |perturbed(t) - baseline(t)| >= threshold, or None
    """
    if not time_series:
        return []

    # Gather all neuron IDs present in the time series
    all_neuron_ids = set()
    for state in time_series:
        all_neuron_ids.update(state.neuron_activity.keys())
    for state in baseline_time_series:
        all_neuron_ids.update(state.neuron_activity.keys())

    # Build parallel time arrays
    times = [s.time for s in time_series]
    baseline_by_time: Dict[float, Dict[str, float]] = {
        s.time: s.neuron_activity for s in baseline_time_series
    }

    results: List[TemporalNeuronMetrics] = []

    for nid in sorted(all_neuron_ids):
        p_activities = [s.neuron_activity.get(nid, 0.0) for s in time_series]

        init_act = p_activities[0] if p_activities else 0.0
        final_act = p_activities[-1] if p_activities else 0.0
        max_act = max(p_activities) if p_activities else 0.0
        min_act = min(p_activities) if p_activities else 0.0

        # Calculate deltas over time
        peak_abs_change = 0.0
        time_of_peak = times[0] if times else 0.0
        time_to_thresh: Optional[float] = None

        for t, p_val in zip(times, p_activities):
            base_val = baseline_by_time.get(t, {}).get(nid, 0.0)
            diff = abs(p_val - base_val)

            if diff > peak_abs_change:
                peak_abs_change = diff
                time_of_peak = t

            if time_to_thresh is None and diff >= threshold:
                time_to_thresh = t

        # Numerical integration (trapezoidal rule) for AUC
        auc = 0.0
        if len(times) >= 2:
            for i in range(len(times) - 1):
                dt = times[i + 1] - times[i]
                if dt > 0:
                    avg_act = 0.5 * (p_activities[i] + p_activities[i + 1])
                    auc += avg_act * dt

        results.append(
            TemporalNeuronMetrics(
                neuron_id=nid,
                initial_activity=round(init_act, 4),
                final_activity=round(final_act, 4),
                max_activity=round(max_act, 4),
                min_activity=round(min_act, 4),
                peak_absolute_change=round(peak_abs_change, 4),
                time_of_peak_change=round(time_of_peak, 4),
                area_under_curve=round(auc, 4),
                time_to_threshold=round(time_to_thresh, 4) if time_to_thresh is not None else None,
            )
        )

    return results
