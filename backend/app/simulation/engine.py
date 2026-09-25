"""
Discrete-time Neural Perturbation Simulation Engine for Drosophila-NeuroAtlas Phase 5.

Computational Model:
- Discrete-time propagation on a directed graph:
    propagated_input[j] = propagation_strength * sum_{i in pre(j)} (w_ij / W_in[j]) * a[i]
    a_next[j] = decay * a[j] + (1 - decay) * baseline_activity + propagated_input[j]
- Active perturbation application:
    For active perturbations at time t:
      activation / excitation:  a[j] = a_next[j] + magnitude
      inhibition / suppression: a[j] = a_next[j] - magnitude
      edge_weight_modification: outgoing edge weights scaled by (1 - magnitude)
- Bounded activity clamping:
    a[j] in [min_activity, max_activity] (default [0.0, 1.0])
- Explicit tracking of:
    - baseline vs perturbed simulation states
    - delta activity = perturbed - baseline
    - propagation hop distances from target neurons
    - network-level summary metrics
    - simulation provenance

SCIENTIFIC DISCLAIMER:
This simulation is a COMPUTATIONAL NETWORK MODEL and does NOT reproduce
experimentally measured neuronal electrophysiology or action potential dynamics.
"""
from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Set, Tuple, Union
import uuid

import networkx as nx

from ..models.connectome import Connection, Neuron, SubgraphResponse
from ..models.simulation import (
    NetworkMetrics,
    NeuralPerturbation,
    NeuronDelta,
    PerturbationEffect,
    PropagationHopRecord,
    SimulationConfig,
    SimulationProvenance,
    SimulationResult,
    SimulationState,
)

MAX_SIMULATION_NEURONS = 500
MAX_PERTURBATIONS = 20
MAX_TIMESTEPS = 1000


class SimulationEngine:
    """
    SimulationEngine implementation conforming to Section 29 of AGENTS.md:
        - initialize(graph, perturbations)
        - step(dt)
        - run(duration)
        - get_state()
        - get_metrics()
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.graph: nx.DiGraph = nx.DiGraph()
        self.perturbations: List[NeuralPerturbation] = []
        self.current_time: float = 0.0
        self.activity: Dict[str, float] = {}
        self.history: List[SimulationState] = []
        self.metadata_source: Dict[str, any] = {}

    def initialize(
        self,
        graph: Union[nx.DiGraph, SubgraphResponse, Dict[str, any]],
        perturbations: Optional[List[NeuralPerturbation]] = None,
        config: Optional[SimulationConfig] = None,
        metadata_source: Optional[Dict[str, any]] = None,
    ) -> None:
        """
        Initialize the simulation engine with a connectome graph and perturbations.
        Enforces conservative bounds (<= 500 neurons, <= 20 perturbations).
        """
        if config is not None:
            self.config = config

        self.perturbations = perturbations or []
        if len(self.perturbations) > MAX_PERTURBATIONS:
            raise ValueError(
                f"Exceeded maximum allowed perturbations (limit: {MAX_PERTURBATIONS}, "
                f"requested: {len(self.perturbations)})."
            )

        # Validate perturbation models
        for p in self.perturbations:
            if not isinstance(p, NeuralPerturbation):
                raise TypeError(f"Expected NeuralPerturbation, got {type(p).__name__}")

        # Construct / normalize internal NetworkX DiGraph
        self.graph = self._build_graph(graph)

        num_neurons = self.graph.number_of_nodes()
        if num_neurons > MAX_SIMULATION_NEURONS:
            raise ValueError(
                f"Simulation exceeds maximum allowed size of {MAX_SIMULATION_NEURONS} neurons "
                f"(requested: {num_neurons}). Bounded subgraph extraction must be applied."
            )

        self.metadata_source = metadata_source or {}

        # Reset simulation state
        self.current_time = 0.0
        self.activity = {
            node: float(self.config.baseline_activity)
            for node in self.graph.nodes
        }

        # Record initial state
        initial_state = SimulationState(
            time=0.0,
            neuron_activity=dict(self.activity),
            active_perturbations=self._get_active_perturbations(0.0),
        )
        self.history = [initial_state]

    def _build_graph(
        self, graph_input: Union[nx.DiGraph, SubgraphResponse, Dict[str, any]]
    ) -> nx.DiGraph:
        """Normalize graph into a directed NetworkX graph with validated weights and fallback flags."""
        g = nx.DiGraph()

        if isinstance(graph_input, nx.DiGraph):
            g = graph_input.copy()
            # Ensure required attributes exist
            for node, attrs in g.nodes(data=True):
                attrs.setdefault("cell_type", "Unknown")
                attrs.setdefault("region", "Unknown")
                attrs.setdefault("has_coordinates", False)
                attrs.setdefault("x", None)
                attrs.setdefault("y", None)
                attrs.setdefault("z", None)

            for u, v, data in g.edges(data=True):
                w = data.get("weight")
                if w is None or w <= 0:
                    data["weight"] = 1.0
                    data["is_fallback"] = True
                else:
                    data["weight"] = float(w)
                    data["is_fallback"] = data.get("is_fallback", False)
            return g

        # Handle SubgraphResponse or dict with 'neurons' and 'connections'
        if isinstance(graph_input, SubgraphResponse):
            neurons = graph_input.neurons
            connections = graph_input.connections
        elif isinstance(graph_input, dict):
            raw_neurons = graph_input.get("neurons", [])
            neurons = [
                n if isinstance(n, Neuron) else Neuron(**n)
                for n in raw_neurons
            ]
            raw_conns = graph_input.get("connections", [])
            connections = [
                c if isinstance(c, Connection) else Connection(**c)
                for c in raw_conns
            ]
        else:
            raise TypeError(f"Unsupported graph input type: {type(graph_input).__name__}")

        for n in neurons:
            g.add_node(
                n.neuron_id,
                cell_type=n.cell_type,
                region=n.region,
                has_coordinates=n.has_coordinates,
                x=n.x,
                y=n.y,
                z=n.z,
                neurotransmitter=getattr(n, "neurotransmitter", None),
            )

        for c in connections:
            if c.source_neuron in g and c.target_neuron in g:
                weight = float(c.weight)
                is_fallback = False
                if weight <= 0 or math.isnan(weight):
                    weight = 1.0
                    is_fallback = True

                g.add_edge(
                    c.source_neuron,
                    c.target_neuron,
                    weight=weight,
                    is_fallback=is_fallback,
                )

        return g

    def _get_active_perturbations(self, t: float) -> List[NeuralPerturbation]:
        """Find perturbations active at time t: start_time <= t < start_time + duration."""
        active = []
        for p in self.perturbations:
            # Active interval [start_time, start_time + duration)
            if p.start_time <= t < (p.start_time + p.duration):
                active.append(p)
        return active

    def step(self, dt: Optional[float] = None) -> SimulationState:
        """
        Execute one discrete simulation step:
        1. Calculate network propagation.
        2. Apply active perturbations.
        3. Clamp activity to [min_activity, max_activity].
        4. Record state.
        5. Return state.
        """
        step_size = dt if dt is not None else self.config.dt
        if step_size <= 0:
            raise ValueError("Simulation step dt must be positive.")

        current_act = self.activity
        decay = self.config.decay
        baseline = self.config.baseline_activity
        prop_strength = self.config.propagation_strength
        min_act = self.config.min_activity
        max_act = self.config.max_activity

        active_perturbs = self._get_active_perturbations(self.current_time)

        # Check for active edge weight modifications
        edge_weight_modifiers: Dict[str, float] = {}
        for p in active_perturbs:
            if p.effect == PerturbationEffect.EDGE_WEIGHT_MODIFICATION:
                for target_id in p.target_neuron_ids:
                    # Scale down edge transmission by (1 - magnitude)
                    edge_weight_modifiers[target_id] = max(0.0, 1.0 - p.magnitude)

        # 1. Calculate network propagation
        new_activity: Dict[str, float] = {}

        for node in self.graph.nodes:
            in_edges = list(self.graph.in_edges(node, data=True))
            if in_edges:
                # Sum weights of incoming edges, applying edge modifiers if active
                modified_weights = []
                for src, _, data in in_edges:
                    w = data.get("weight", 1.0)
                    mod = edge_weight_modifiers.get(src, 1.0)
                    modified_weights.append((src, w * mod))

                total_in_weight = sum(w for _, w in modified_weights)
                if total_in_weight > 0:
                    propagated_input = prop_strength * sum(
                        (w / total_in_weight) * (current_act.get(src, baseline) - baseline)
                        for src, w in modified_weights
                    )
                else:
                    propagated_input = 0.0
            else:
                propagated_input = 0.0

            # Passive decay toward resting baseline + input
            curr = current_act.get(node, baseline)
            a_next = baseline + (decay * (curr - baseline)) + propagated_input
            new_activity[node] = a_next

        # 2. Apply active perturbations
        for p in active_perturbs:
            for target_id in p.target_neuron_ids:
                if target_id in new_activity:
                    if p.effect in (PerturbationEffect.ACTIVATION, PerturbationEffect.EXCITATION):
                        new_activity[target_id] += p.magnitude
                    elif p.effect in (PerturbationEffect.INHIBITION, PerturbationEffect.SUPPRESSION):
                        new_activity[target_id] -= p.magnitude

        # 3. Clamp activity to bounds
        for node in new_activity:
            val = new_activity[node]
            if val < min_act:
                val = min_act
            elif val > max_act:
                val = max_act
            new_activity[node] = float(val)

        # Advance simulation time
        self.current_time = round(self.current_time + step_size, 6)
        self.activity = new_activity

        # 4. Record state
        state = SimulationState(
            time=self.current_time,
            neuron_activity=dict(self.activity),
            active_perturbations=list(active_perturbs),
        )
        self.history.append(state)
        return state

    def run(self, duration: Optional[float] = None) -> List[SimulationState]:
        """Run the simulation for the specified duration (or config.duration)."""
        total_duration = duration if duration is not None else self.config.duration
        if total_duration <= 0 or total_duration > self.config.duration + 50.0:
            raise ValueError(f"Duration must be between 0.1 and 50.0 seconds (got {total_duration}).")

        dt = self.config.dt
        num_steps = int(round(total_duration / dt))
        if num_steps > MAX_TIMESTEPS:
            raise ValueError(
                f"Simulation exceeds maximum timestep limit of {MAX_TIMESTEPS} steps "
                f"(requested: {num_steps}). Increase dt or decrease duration."
            )

        for _ in range(num_steps):
            self.step(dt)

        return self.history

    def get_state(self) -> SimulationState:
        """Return the current simulation state."""
        return SimulationState(
            time=self.current_time,
            neuron_activity=dict(self.activity),
            active_perturbations=self._get_active_perturbations(self.current_time),
        )

    def get_metrics(self) -> NetworkMetrics:
        """Calculate network-level computational metrics for the current state."""
        if not self.activity:
            return NetworkMetrics(
                mean_activity=0.0,
                active_neuron_count=0,
                maximum_activity=0.0,
                minimum_activity=0.0,
                total_network_activity=0.0,
                perturbed_neuron_activity={},
                downstream_affected_neuron_count=0,
            )

        activities = list(self.activity.values())
        mean_act = sum(activities) / len(activities)
        max_act = max(activities)
        min_act = min(activities)
        total_act = sum(activities)

        baseline = self.config.baseline_activity
        # Count neurons whose activity meaningfully exceeds baseline
        active_count = sum(1 for a in activities if a > (baseline + 0.05))

        target_set: Set[str] = set()
        for p in self.perturbations:
            target_set.update(p.target_neuron_ids)

        perturbed_act = {
            nid: self.activity[nid]
            for nid in target_set
            if nid in self.activity
        }

        # Calculate affected non-target neurons
        affected_count = sum(
            1 for nid, a in self.activity.items()
            if nid not in target_set and abs(a - baseline) > 0.01
        )

        return NetworkMetrics(
            mean_activity=round(mean_act, 4),
            active_neuron_count=active_count,
            maximum_activity=round(max_act, 4),
            minimum_activity=round(min_act, 4),
            total_network_activity=round(total_act, 4),
            perturbed_neuron_activity={k: round(v, 4) for k, v in perturbed_act.items()},
            downstream_affected_neuron_count=affected_count,
        )

    def compute_hop_distances(self) -> Dict[str, Optional[int]]:
        """Compute shortest directed hop distances from perturbation targets to all neurons."""
        target_set = {
            t for p in self.perturbations
            for t in p.target_neuron_ids
            if t in self.graph
        }
        if not target_set:
            return {node: None for node in self.graph.nodes}

        hop_distances: Dict[str, Optional[int]] = {node: None for node in self.graph.nodes}

        for target in target_set:
            try:
                lengths = nx.single_source_shortest_path_length(self.graph, target)
                for node, dist in lengths.items():
                    curr = hop_distances.get(node)
                    if curr is None or dist < curr:
                        hop_distances[node] = dist
            except Exception:
                pass

        return hop_distances

    def run_comparison(self, duration: Optional[float] = None) -> SimulationResult:
        """
        Run both baseline (unperturbed) and perturbed simulations under identical
        conditions, returning complete comparison deltas and provenance.
        """
        sim_duration = duration if duration is not None else self.config.duration
        sim_id = f"sim_{uuid.uuid4().hex[:12]}"

        # 1. Run Baseline (no perturbations)
        baseline_engine = SimulationEngine(config=self.config)
        baseline_engine.initialize(
            graph=self.graph,
            perturbations=[],
            config=self.config,
            metadata_source=self.metadata_source,
        )
        baseline_history = baseline_engine.run(sim_duration)
        baseline_final_state = baseline_engine.get_state()
        baseline_metrics = baseline_engine.get_metrics()

        # 2. Run Perturbed (with configured perturbations)
        self.initialize(
            graph=self.graph,
            perturbations=self.perturbations,
            config=self.config,
            metadata_source=self.metadata_source,
        )
        perturbed_history = self.run(sim_duration)
        perturbed_final_state = self.get_state()
        perturbed_metrics = self.get_metrics()

        # 3. Compute hop distances
        hop_distances = self.compute_hop_distances()

        # 4. Compute neuron-by-neuron deltas
        deltas: List[NeuronDelta] = []
        for node in self.graph.nodes:
            attrs = self.graph.nodes[node]
            base_a = baseline_final_state.neuron_activity.get(node, self.config.baseline_activity)
            pert_a = perturbed_final_state.neuron_activity.get(node, self.config.baseline_activity)
            delta = round(pert_a - base_a, 4)

            deltas.append(
                NeuronDelta(
                    neuron_id=node,
                    cell_type=attrs.get("cell_type", "Unknown"),
                    region=attrs.get("region", "Unknown"),
                    baseline_activity=round(base_a, 4),
                    perturbed_activity=round(pert_a, 4),
                    delta_activity=delta,
                    hop_distance=hop_distances.get(node),
                    has_coordinates=attrs.get("has_coordinates", False),
                    x=attrs.get("x"),
                    y=attrs.get("y"),
                    z=attrs.get("z"),
                )
            )

        # Sort deltas by magnitude of activity change descending
        deltas.sort(key=lambda d: abs(d.delta_activity), reverse=True)

        # 5. Track temporal propagation along hops
        propagation_records: List[PropagationHopRecord] = []
        target_ids = {t for p in self.perturbations for t in p.target_neuron_ids}

        for node in self.graph.nodes:
            first_change_time = None
            final_change = 0.0

            # Scan time series for first time |pert - base| > 0.01
            for p_state, b_state in zip(perturbed_history, baseline_history):
                p_val = p_state.neuron_activity.get(node, 0.0)
                b_val = b_state.neuron_activity.get(node, 0.0)
                diff = p_val - b_val
                if abs(diff) > 0.01:
                    if first_change_time is None:
                        first_change_time = p_state.time
                    final_change = diff

            if first_change_time is not None or node in target_ids:
                propagation_records.append(
                    PropagationHopRecord(
                        neuron_id=node,
                        hop_distance=hop_distances.get(node),
                        activity_change=round(final_change, 4),
                        time_of_change=first_change_time,
                    )
                )

        # Sort propagation records by hop distance then time
        propagation_records.sort(
            key=lambda r: (
                r.hop_distance if r.hop_distance is not None else 999,
                r.time_of_change if r.time_of_change is not None else 999.0,
            )
        )

        # 6. Provenance metadata
        is_synthetic = self.metadata_source.get("is_synthetic", True)
        provider_name = self.metadata_source.get("provider_type", "synthetic" if is_synthetic else "real")
        dataset_name = self.metadata_source.get("dataset_name", "synthetic" if is_synthetic else "cns")
        dataset_version = self.metadata_source.get("dataset_version", "v1.0" if not is_synthetic else None)

        provenance = SimulationProvenance(
            simulation_id=sim_id,
            connectome_provider=provider_name,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            is_synthetic=is_synthetic,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            model_version="0.1.0-phase5",
            neuron_count=self.graph.number_of_nodes(),
            connection_count=self.graph.number_of_edges(),
            config=self.config,
            perturbations=self.perturbations,
        )

        return SimulationResult(
            simulation_id=sim_id,
            config=self.config,
            time_series=perturbed_history,
            baseline_time_series=baseline_history,
            final_state=perturbed_final_state,
            baseline_final_state=baseline_final_state,
            metrics=perturbed_metrics,
            baseline_metrics=baseline_metrics,
            neuron_deltas=deltas,
            propagation_records=propagation_records,
            provenance=provenance,
            was_truncated=False,
        )
