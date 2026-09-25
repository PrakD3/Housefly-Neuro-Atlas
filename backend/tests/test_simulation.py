"""
Comprehensive Phase 5 Backend Tests — Neural Perturbation Engine.

Covers:
1. simulation initialization
2. baseline simulation
3. activation perturbation
4. inhibition perturbation
5. multiple target neurons
6. bounded activity [0,1]
7. deterministic repeated simulation
8. timestep handling
9. duration handling
10. propagation through one hop
11. propagation through multiple hops
12. baseline vs perturbed comparison
13. network metrics
14. invalid perturbation rejection
15. excessive simulation size rejection
16. provenance preservation
17. synthetic provider compatibility
18. real provider normalized-subgraph compatibility
19. scientific validation sanity checks (6 rules)
20. API endpoints (POST /simulations, GET /simulations/{id}, GET /results, POST /run, error handling)
"""
import copy
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import networkx as nx

from app.main import app
from app.models.connectome import Connection, Neuron, SubgraphResponse
from app.models.simulation import (
    NetworkMetrics,
    NeuralPerturbation,
    PerturbationEffect,
    SimulationConfig,
    SimulationResult,
    SimulationRunRequest,
)
from app.simulation.engine import (
    MAX_PERTURBATIONS,
    MAX_SIMULATION_NEURONS,
    SimulationEngine,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def linear_graph():
    """Deterministic linear 4-neuron graph: N0 -> N1 -> N2 -> N3."""
    neurons = [
        Neuron(neuron_id="N0", cell_type="Sensory", region="AL", has_coordinates=True, x=0.0, y=0.0, z=0.0),
        Neuron(neuron_id="N1", cell_type="Interneuron", region="LH", has_coordinates=True, x=10.0, y=0.0, z=0.0),
        Neuron(neuron_id="N2", cell_type="Projection", region="MB", has_coordinates=False, x=None, y=None, z=None),
        Neuron(neuron_id="N3", cell_type="Motor", region="VNC", has_coordinates=True, x=30.0, y=0.0, z=0.0),
    ]
    connections = [
        Connection(source_neuron="N0", target_neuron="N1", weight=2.0),
        Connection(source_neuron="N1", target_neuron="N2", weight=3.0),
        Connection(source_neuron="N2", target_neuron="N3", weight=1.5),
    ]
    return SubgraphResponse(neurons=neurons, connections=connections)


# =====================================================================
# Unit Tests for SimulationEngine
# =====================================================================

def test_simulation_initialization(linear_graph):
    """1. Engine initializes with graph, baseline activity, and zero time."""
    engine = SimulationEngine()
    engine.initialize(linear_graph, perturbations=[])

    state = engine.get_state()
    assert state.time == 0.0
    assert len(state.neuron_activity) == 4
    for nid in ["N0", "N1", "N2", "N3"]:
        assert state.neuron_activity[nid] == pytest.approx(0.2)  # default baseline_activity
    assert len(state.active_perturbations) == 0


def test_baseline_simulation(linear_graph):
    """2. Baseline simulation with no perturbations runs deterministically."""
    engine = SimulationEngine()
    engine.initialize(linear_graph, perturbations=[])
    history = engine.run(duration=1.0)

    assert len(history) == 11  # initial + 10 steps of dt=0.1
    final_state = engine.get_state()
    assert final_state.time == pytest.approx(1.0)
    for act in final_state.neuron_activity.values():
        assert 0.0 <= act <= 1.0


def test_activation_perturbation(linear_graph):
    """3. Activation perturbation increases target neuron's activity above baseline."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.6,
        start_time=0.0,
        duration=2.0,
    )
    result = SimulationEngine().run_comparison()  # default empty check
    engine = SimulationEngine(SimulationConfig(baseline_activity=0.2))
    engine.initialize(linear_graph, perturbations=[pert])
    comp_result = engine.run_comparison(duration=2.0)

    n0_delta = next(d for d in comp_result.neuron_deltas if d.neuron_id == "N0")
    assert n0_delta.perturbed_activity > n0_delta.baseline_activity
    assert n0_delta.delta_activity > 0.0


def test_inhibition_perturbation(linear_graph):
    """4. Inhibition perturbation decreases target neuron's activity below baseline."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.INHIBITION,
        magnitude=0.5,
        start_time=0.0,
        duration=2.0,
    )
    engine = SimulationEngine(SimulationConfig(baseline_activity=0.3))
    engine.initialize(linear_graph, perturbations=[pert])
    comp_result = engine.run_comparison(duration=2.0)

    n0_delta = next(d for d in comp_result.neuron_deltas if d.neuron_id == "N0")
    assert n0_delta.perturbed_activity < n0_delta.baseline_activity
    assert n0_delta.delta_activity < 0.0


def test_multiple_target_neurons(linear_graph):
    """5. Perturbation targeting multiple neurons simultaneously affects all targets."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0", "N1"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.5,
        start_time=0.0,
        duration=1.0,
    )
    engine = SimulationEngine()
    engine.initialize(linear_graph, perturbations=[pert])
    result = engine.run_comparison(duration=1.0)

    deltas_by_id = {d.neuron_id: d for d in result.neuron_deltas}
    assert deltas_by_id["N0"].delta_activity > 0.0
    assert deltas_by_id["N1"].delta_activity > 0.0


def test_bounded_activity_zero_to_one(linear_graph):
    """6. Modeled activity never exceeds [0.0, 1.0] under extreme perturbation."""
    extreme_act = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=1.0,
        duration=5.0,
    )
    config = SimulationConfig(propagation_strength=5.0, decay=1.0)
    engine = SimulationEngine(config)
    engine.initialize(linear_graph, perturbations=[extreme_act])
    engine.run(duration=3.0)

    for state in engine.history:
        for val in state.neuron_activity.values():
            assert 0.0 <= val <= 1.0

    # Extreme inhibition clamped to 0.0
    extreme_inh = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.INHIBITION,
        magnitude=1.0,
        duration=5.0,
    )
    engine_inh = SimulationEngine(config)
    engine_inh.initialize(linear_graph, perturbations=[extreme_inh])
    engine_inh.run(duration=3.0)
    for state in engine_inh.history:
        for val in state.neuron_activity.values():
            assert 0.0 <= val <= 1.0


def test_deterministic_repeated_simulation(linear_graph):
    """7. Repeated runs with same graph, config, and perturbations produce identical results."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.4,
        duration=2.0,
    )
    engine1 = SimulationEngine(SimulationConfig(dt=0.1, duration=2.0))
    engine1.initialize(linear_graph, [pert])
    res1 = engine1.run_comparison()

    engine2 = SimulationEngine(SimulationConfig(dt=0.1, duration=2.0))
    engine2.initialize(linear_graph, [pert])
    res2 = engine2.run_comparison()

    assert len(res1.time_series) == len(res2.time_series)
    for s1, s2 in zip(res1.time_series, res2.time_series):
        assert s1.time == s2.time
        assert s1.neuron_activity == s2.neuron_activity

    assert len(res1.neuron_deltas) == len(res2.neuron_deltas)
    for d1, d2 in zip(res1.neuron_deltas, res2.neuron_deltas):
        assert d1.neuron_id == d2.neuron_id
        assert d1.delta_activity == d2.delta_activity


def test_timestep_handling(linear_graph):
    """8. Different valid timesteps dt advance simulation time correctly."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.3,
        duration=1.0,
    )
    engine = SimulationEngine(SimulationConfig(dt=0.05, duration=1.0))
    engine.initialize(linear_graph, [pert])
    history = engine.run()
    # 1.0 / 0.05 = 20 steps + initial state = 21
    assert len(history) == 21
    assert history[-1].time == pytest.approx(1.0)


def test_duration_handling(linear_graph):
    """9. Duration control limits the total simulation span."""
    engine = SimulationEngine(SimulationConfig(dt=0.2, duration=3.0))
    engine.initialize(linear_graph, [])
    history = engine.run(duration=2.0)
    assert history[-1].time == pytest.approx(2.0)


def test_propagation_through_one_hop(linear_graph):
    """10. Perturbation on N0 propagates downstream to 1-hop neighbor N1."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.7,
        duration=2.0,
    )
    engine = SimulationEngine(SimulationConfig(propagation_strength=0.8, baseline_activity=0.1))
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=2.0)

    n1_delta = next(d for d in res.neuron_deltas if d.neuron_id == "N1")
    assert n1_delta.hop_distance == 1
    assert n1_delta.delta_activity > 0.0


def test_propagation_through_multiple_hops(linear_graph):
    """11. Perturbation on N0 propagates to multi-hop downstream neighbors N2 and N3."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.8,
        duration=3.0,
    )
    engine = SimulationEngine(SimulationConfig(propagation_strength=0.8, baseline_activity=0.1))
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=3.0)

    deltas = {d.neuron_id: d for d in res.neuron_deltas}
    assert deltas["N1"].hop_distance == 1
    assert deltas["N2"].hop_distance == 2
    assert deltas["N3"].hop_distance == 3

    # Check propagation record tracks time and hop order
    hop_order = [r.hop_distance for r in res.propagation_records if r.hop_distance is not None]
    assert 0 in hop_order
    assert 1 in hop_order


def test_baseline_vs_perturbed_comparison(linear_graph):
    """12. run_comparison calculates delta_activity = perturbed - baseline for all neurons."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.5,
        duration=2.0,
    )
    engine = SimulationEngine()
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=2.0)

    assert len(res.neuron_deltas) == 4
    for d in res.neuron_deltas:
        assert d.delta_activity == pytest.approx(d.perturbed_activity - d.baseline_activity, abs=1e-4)


def test_network_metrics_calculation(linear_graph):
    """13. NetworkMetrics calculates mean, total, max, min, and affected counts."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.5,
        duration=2.0,
    )
    engine = SimulationEngine()
    engine.initialize(linear_graph, [pert])
    engine.run(duration=1.0)
    metrics = engine.get_metrics()

    assert isinstance(metrics, NetworkMetrics)
    assert 0.0 <= metrics.mean_activity <= 1.0
    assert metrics.total_network_activity >= metrics.mean_activity
    assert metrics.maximum_activity >= metrics.minimum_activity
    assert "N0" in metrics.perturbed_neuron_activity


def test_invalid_perturbation_rejection():
    """14. Pydantic validation rejects invalid perturbation effects and parameters."""
    with pytest.raises(Exception):
        NeuralPerturbation(
            target_neuron_ids=["N0"],
            effect="invalid_effect_name",
            magnitude=0.5,
            duration=1.0,
        )

    with pytest.raises(Exception):
        NeuralPerturbation(
            target_neuron_ids=[],  # empty targets
            effect=PerturbationEffect.ACTIVATION,
            magnitude=0.5,
            duration=1.0,
        )

    with pytest.raises(Exception):
        NeuralPerturbation(
            target_neuron_ids=["N0"],
            effect=PerturbationEffect.ACTIVATION,
            magnitude=1.5,  # > 1.0
            duration=1.0,
        )


def test_excessive_simulation_size_rejection():
    """15. Simulation rejects subgraphs exceeding MAX_SIMULATION_NEURONS (500)."""
    large_graph = nx.DiGraph()
    for i in range(501):
        large_graph.add_node(f"node_{i}", cell_type="Interneuron", region="Brain")

    engine = SimulationEngine()
    with pytest.raises(ValueError, match="exceeds maximum allowed size of 500 neurons"):
        engine.initialize(large_graph, [])


def test_provenance_preservation(linear_graph):
    """16. Provenance metadata is fully retained in SimulationResult."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.5,
        duration=1.0,
    )
    engine = SimulationEngine()
    meta = {
        "provider_type": "real",
        "is_synthetic": False,
        "dataset_name": "cns",
        "dataset_version": "v1.0",
    }
    engine.initialize(linear_graph, [pert], metadata_source=meta)
    res = engine.run_comparison(duration=1.0)

    prov = res.provenance
    assert prov.connectome_provider == "real"
    assert prov.is_synthetic is False
    assert prov.dataset_name == "cns"
    assert prov.dataset_version == "v1.0"
    assert prov.neuron_count == 4
    assert prov.connection_count == 3
    assert len(prov.perturbations) == 1


# =====================================================================
# Scientific Sanity Tests (Section 21)
# =====================================================================

def test_sanity_no_perturbation_preserves_baseline(linear_graph):
    """Rule 1: No perturbation must produce delta = 0 across all neurons."""
    engine = SimulationEngine()
    engine.initialize(linear_graph, perturbations=[])
    res = engine.run_comparison(duration=2.0)

    for delta in res.neuron_deltas:
        assert delta.delta_activity == pytest.approx(0.0, abs=1e-4)


def test_sanity_positive_activation_increases_target(linear_graph):
    """Rule 2: Activation perturbation increases target's modeled activity."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.4,
        duration=2.0,
    )
    engine = SimulationEngine()
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=2.0)
    n0 = next(d for d in res.neuron_deltas if d.neuron_id == "N0")
    assert n0.delta_activity > 0.0


def test_sanity_inhibition_decreases_target(linear_graph):
    """Rule 3: Inhibition perturbation decreases target's modeled activity."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.INHIBITION,
        magnitude=0.3,
        duration=2.0,
    )
    engine = SimulationEngine(SimulationConfig(baseline_activity=0.3))
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=2.0)
    n0 = next(d for d in res.neuron_deltas if d.neuron_id == "N0")
    assert n0.delta_activity < 0.0


def test_sanity_zero_propagation_prevents_downstream_effects(linear_graph):
    """Rule 4: With propagation_strength=0.0, downstream neurons experience zero delta."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.8,
        duration=2.0,
    )
    engine = SimulationEngine(SimulationConfig(propagation_strength=0.0))
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=2.0)

    for d in res.neuron_deltas:
        if d.neuron_id != "N0":
            assert d.delta_activity == pytest.approx(0.0, abs=1e-4)


def test_sanity_increasing_propagation_increases_downstream_effect(linear_graph):
    """Rule 5: Increasing propagation strength produces larger modeled downstream effect."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.3,
        duration=1.0,
    )

    # Low propagation
    engine_low = SimulationEngine(SimulationConfig(propagation_strength=0.1, baseline_activity=0.1))
    engine_low.initialize(linear_graph, [pert])
    res_low = engine_low.run_comparison(duration=0.5)
    n1_low = next(d for d in res_low.neuron_deltas if d.neuron_id == "N1")

    # High propagation
    engine_high = SimulationEngine(SimulationConfig(propagation_strength=0.6, baseline_activity=0.1))
    engine_high.initialize(linear_graph, [pert])
    res_high = engine_high.run_comparison(duration=0.5)
    n1_high = next(d for d in res_high.neuron_deltas if d.neuron_id == "N1")

    assert n1_high.delta_activity > n1_low.delta_activity


def test_null_coordinates_preserved_in_simulation(linear_graph):
    """Neurons with missing somaLocation retain has_coordinates=False and None coordinates in deltas."""
    pert = NeuralPerturbation(
        target_neuron_ids=["N0"],
        effect=PerturbationEffect.ACTIVATION,
        magnitude=0.5,
        duration=1.0,
    )
    engine = SimulationEngine()
    engine.initialize(linear_graph, [pert])
    res = engine.run_comparison(duration=1.0)

    n2_delta = next(d for d in res.neuron_deltas if d.neuron_id == "N2")
    assert n2_delta.has_coordinates is False
    assert n2_delta.x is None
    assert n2_delta.y is None
    assert n2_delta.z is None


# =====================================================================
# API Integration Tests
# =====================================================================

def test_api_create_simulation_synthetic_default(client):
    """POST /simulations with default synthetic graph creates and runs simulation."""
    payload = {
        "perturbations": [
            {
                "target_neuron_ids": ["syn_neuron_0"],
                "effect": "activation",
                "magnitude": 0.5,
                "duration": 2.0,
                "start_time": 0.0,
            }
        ]
    }
    resp = client.post("/simulations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "simulation_id" in data
    assert "time_series" in data
    assert "baseline_time_series" in data
    assert "neuron_deltas" in data
    assert "metrics" in data
    assert "provenance" in data
    assert data["provenance"]["is_synthetic"] is True


def test_api_create_simulation_with_focal_neuron(client):
    """POST /simulations with focal_neuron_id and hops extracts neighborhood and runs."""
    payload = {
        "focal_neuron_id": "syn_neuron_0",
        "hops": 1,
        "perturbations": [
            {
                "target_neuron_ids": ["syn_neuron_0"],
                "effect": "inhibition",
                "magnitude": 0.4,
                "duration": 1.5,
                "start_time": 0.0,
            }
        ],
    }
    resp = client.post("/simulations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["neuron_deltas"]) > 0


def test_api_get_simulation_by_id(client):
    """GET /simulations/{id} retrieves stored simulation results."""
    # First create one
    payload = {
        "focal_neuron_id": "syn_neuron_1",
        "hops": 1,
        "perturbations": [
            {
                "target_neuron_ids": ["syn_neuron_1"],
                "effect": "activation",
                "magnitude": 0.5,
                "duration": 1.0,
            }
        ],
    }
    create_resp = client.post("/simulations", json=payload)
    assert create_resp.status_code == 201
    sim_id = create_resp.json()["simulation_id"]

    get_resp = client.get(f"/simulations/{sim_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["simulation_id"] == sim_id

    # Test /results alias
    alias_resp = client.get(f"/simulations/{sim_id}/results")
    assert alias_resp.status_code == 200
    assert alias_resp.json()["simulation_id"] == sim_id


def test_api_get_simulation_404(client):
    """GET /simulations/{id} returns 404 for unknown simulation ID."""
    resp = client.get("/simulations/unknown_sim_id_123")
    assert resp.status_code == 404


def test_api_rerun_simulation(client):
    """POST /simulations/{id}/run allows re-running with modified duration."""
    payload = {
        "focal_neuron_id": "syn_neuron_2",
        "hops": 1,
        "perturbations": [
            {
                "target_neuron_ids": ["syn_neuron_2"],
                "effect": "activation",
                "magnitude": 0.5,
                "duration": 1.0,
            }
        ],
    }
    create_resp = client.post("/simulations", json=payload)
    assert create_resp.status_code == 201
    sim_id = create_resp.json()["simulation_id"]

    rerun_resp = client.post(f"/simulations/{sim_id}/run?duration=2.0")
    assert rerun_resp.status_code == 200
    data = rerun_resp.json()
    assert data["final_state"]["time"] == pytest.approx(2.0)


def test_api_rejects_excessive_perturbations(client):
    """POST /simulations rejects more than MAX_PERTURBATIONS (20)."""
    pert_list = [
        {
            "target_neuron_ids": ["syn_neuron_0"],
            "effect": "activation",
            "magnitude": 0.1,
            "duration": 1.0,
        }
        for _ in range(MAX_PERTURBATIONS + 1)
    ]
    resp = client.post("/simulations", json={"perturbations": pert_list})
    assert resp.status_code == 400
    assert "Exceeded maximum allowed perturbations" in resp.json()["detail"]
