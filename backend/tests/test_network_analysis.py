"""
Unit and integration tests for Phase 6 Network Analysis Engine.

Covers:
1. Structural metrics (node count, edge count, density, degrees, components, paths)
2. Centrality metrics (in-degree, out-degree, betweenness, closeness)
3. Target-centered reachability and multi-hop paths
4. Baseline vs perturbed activity deltas
5. Threshold filtering for model-affected neurons
6. Temporal dynamic metrics (AUC, peak delta, time to threshold)
7. Edge cases: empty graph, single-node graph, disconnected graph, 0-edge graph
8. Mathematical fixture validation (A -> B -> C exact values)
9. Graph bounds safeguards (MAX_ANALYSIS_NODES, MAX_ANALYSIS_EDGES)
10. Provenance preservation
11. Compatibility with synthetic and real connectome subgraphs
12. API endpoints: POST /analysis/network and GET /analysis/network/{simulation_id}
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
import networkx as nx

from app.api.simulation import _store_simulation, clear_simulation_cache
from app.main import app
from app.models.connectome import Connection, Neuron, SubgraphResponse
from app.models.network import (
    GraphStructuralMetrics,
    NetworkAnalysisRequest,
    NetworkAnalysisResult,
)
from app.models.simulation import (
    NetworkMetrics,
    NeuralPerturbation,
    NeuronDelta,
    PerturbationEffect,
    SimulationConfig,
    SimulationProvenance,
    SimulationResult,
    SimulationState,
)
from app.network.centrality import compute_centrality_metrics
from app.network.engine import (
    MAX_ANALYSIS_EDGES,
    MAX_ANALYSIS_NODES,
    NetworkAnalysisEngine,
)
from app.network.metrics import compute_structural_metrics
from app.network.paths import compute_target_analysis
from app.network.perturbation import compute_perturbation_analysis
from app.network.temporal import compute_temporal_metrics
from app.simulation.engine import SimulationEngine

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_cache():
    clear_simulation_cache()
    yield
    clear_simulation_cache()


def _create_mock_simulation_result(
    sim_id: str = "sim_test_001",
    node_ids: list = None,
    target_ids: list = None,
    baseline_val: float = 0.2,
    perturbed_map: dict = None,
    is_synthetic: bool = True,
) -> SimulationResult:
    """Helper to create a well-formed mock SimulationResult."""
    if node_ids is None:
        node_ids = ["A", "B", "C"]
    if target_ids is None:
        target_ids = ["A"]
    if perturbed_map is None:
        perturbed_map = {"A": 0.8, "B": 0.5, "C": 0.3}

    t0_state = SimulationState(
        time=0.0,
        neuron_activity={nid: baseline_val for nid in node_ids},
    )
    t1_state = SimulationState(
        time=1.0,
        neuron_activity={nid: perturbed_map.get(nid, baseline_val) for nid in node_ids},
    )
    b0_state = SimulationState(
        time=0.0,
        neuron_activity={nid: baseline_val for nid in node_ids},
    )
    b1_state = SimulationState(
        time=1.0,
        neuron_activity={nid: baseline_val for nid in node_ids},
    )

    deltas = []
    for nid in node_ids:
        base_a = baseline_val
        pert_a = perturbed_map.get(nid, baseline_val)
        deltas.append(
            NeuronDelta(
                neuron_id=nid,
                cell_type="TestType",
                region="TestRegion",
                baseline_activity=base_a,
                perturbed_activity=pert_a,
                delta_activity=round(pert_a - base_a, 4),
                hop_distance=0 if nid in target_ids else 1,
                has_coordinates=True,
                x=0.0,
                y=0.0,
                z=0.0,
            )
        )

    prov = SimulationProvenance(
        simulation_id=sim_id,
        connectome_provider="synthetic_test",
        dataset_name="synthetic",
        dataset_version=None,
        is_synthetic=is_synthetic,
        creation_timestamp=datetime.now(timezone.utc).isoformat(),
        neuron_count=len(node_ids),
        connection_count=2,
        config=SimulationConfig(),
        perturbations=[
            NeuralPerturbation(
                target_neuron_ids=target_ids,
                effect=PerturbationEffect.ACTIVATION,
                magnitude=0.6,
                start_time=0.0,
                duration=1.0,
            )
        ],
    )

    metrics = NetworkMetrics(
        mean_activity=0.5,
        active_neuron_count=len(node_ids),
        maximum_activity=0.8,
        minimum_activity=0.2,
        total_network_activity=1.6,
        perturbed_neuron_activity={t: perturbed_map.get(t, 0.8) for t in target_ids},
        downstream_affected_neuron_count=2,
    )

    return SimulationResult(
        simulation_id=sim_id,
        config=SimulationConfig(),
        time_series=[t0_state, t1_state],
        baseline_time_series=[b0_state, b1_state],
        final_state=t1_state,
        baseline_final_state=b1_state,
        metrics=metrics,
        baseline_metrics=metrics,
        neuron_deltas=deltas,
        propagation_records=[],
        provenance=prov,
    )


# ---------------------------------------------------------------------------
# 1-7: Structural & Centrality Metrics
# ---------------------------------------------------------------------------


def test_structural_metrics_basic_graph():
    """Verify standard structural metrics on a 3-node directed graph."""
    g = nx.DiGraph()
    g.add_edge("1", "2")
    g.add_edge("2", "3")

    metrics = compute_structural_metrics(g)
    assert metrics.neuron_count == 3
    assert metrics.connection_count == 2
    assert metrics.density == pytest.approx(2.0 / (3 * 2), abs=1e-5)
    assert metrics.mean_in_degree == pytest.approx(2.0 / 3.0, abs=1e-4)
    assert metrics.mean_out_degree == pytest.approx(2.0 / 3.0, abs=1e-4)
    assert metrics.max_in_degree == 1
    assert metrics.max_out_degree == 1
    assert metrics.weakly_connected_components == 1
    assert metrics.largest_wcc_size == 3
    assert metrics.is_directed is True
    assert metrics.is_dag is True


def test_structural_metrics_empty_graph():
    """Verify graceful handling of an empty graph (0 nodes, 0 edges)."""
    g = nx.DiGraph()
    metrics = compute_structural_metrics(g)
    assert metrics.neuron_count == 0
    assert metrics.connection_count == 0
    assert metrics.density == 0.0
    assert metrics.mean_in_degree == 0.0
    assert metrics.average_shortest_path_length is None


def test_structural_metrics_single_node_graph():
    """Verify single-node graph handling."""
    g = nx.DiGraph()
    g.add_node("lone_neuron")
    metrics = compute_structural_metrics(g)
    assert metrics.neuron_count == 1
    assert metrics.connection_count == 0
    assert metrics.density == 0.0
    assert metrics.weakly_connected_components == 1
    assert metrics.largest_wcc_size == 1
    assert metrics.average_shortest_path_length is None


def test_structural_metrics_disconnected_graph():
    """Verify multiple weakly connected components."""
    g = nx.DiGraph()
    g.add_edge("A", "B")
    g.add_edge("C", "D")
    metrics = compute_structural_metrics(g)
    assert metrics.neuron_count == 4
    assert metrics.connection_count == 2
    assert metrics.weakly_connected_components == 2
    assert metrics.largest_wcc_size == 2


def test_centrality_metrics():
    """Verify in-degree, out-degree, betweenness, and closeness centrality."""
    # A -> B -> C
    g = nx.DiGraph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    cent = compute_centrality_metrics(g)
    assert len(cent) == 3
    by_id = {c.neuron_id: c for c in cent}

    # B lies on the only path between A and C, so B has betweenness = 1.0 (normalized for 3 nodes: (n-1)*(n-2) = 2, 2*1/2 = 1.0)
    assert by_id["B"].betweenness_centrality > 0.0
    assert by_id["A"].betweenness_centrality == 0.0
    assert by_id["C"].betweenness_centrality == 0.0

    # In-degree centrality: C has 1 incoming / 2 = 0.5; A has 0
    assert by_id["C"].in_degree_centrality == 0.5
    assert by_id["A"].in_degree_centrality == 0.0
    assert by_id["A"].out_degree_centrality == 0.5
    assert by_id["C"].out_degree_centrality == 0.0


def test_centrality_empty_and_single_node():
    """Verify centrality on 0 and 1 node graphs."""
    assert compute_centrality_metrics(nx.DiGraph()) == []

    g1 = nx.DiGraph()
    g1.add_node("solo")
    cent = compute_centrality_metrics(g1)
    assert len(cent) == 1
    assert cent[0].neuron_id == "solo"
    assert cent[0].betweenness_centrality == 0.0


# ---------------------------------------------------------------------------
# 8-9: Target Reachability & Paths
# ---------------------------------------------------------------------------


def test_target_analysis_reachability():
    """Verify target degree, upstream/downstream partners, and multi-hop reachability."""
    # S -> T -> D1 -> D2
    g = nx.DiGraph()
    g.add_edge("S", "T")
    g.add_edge("T", "D1")
    g.add_edge("D1", "D2")

    target_res = compute_target_analysis(g, target_neuron_ids=["T"], max_hops=3)
    assert len(target_res) == 1
    t = target_res[0]
    assert t.target_neuron_id == "T"
    assert t.in_degree == 1
    assert t.out_degree == 1
    assert t.upstream_neurons == ["S"]
    assert t.downstream_neurons == ["D1"]
    assert t.reachability_by_hop[1] == ["D1"]
    assert t.reachability_by_hop[2] == ["D2"]
    assert t.reachability_counts[1] == 1
    assert t.reachability_counts[2] == 1
    assert t.reachability_counts[3] == 0
    assert t.shortest_path_lengths_downstream == {"D1": 1, "D2": 2}


def test_target_analysis_target_not_in_graph():
    """Verify target that does not exist in the subgraph returns safe zeros."""
    g = nx.DiGraph()
    g.add_edge("A", "B")
    target_res = compute_target_analysis(g, target_neuron_ids=["MISSING"], max_hops=3)
    assert len(target_res) == 1
    t = target_res[0]
    assert t.target_neuron_id == "MISSING"
    assert t.in_degree == 0
    assert t.out_degree == 0
    assert t.downstream_neuron_count == 0


# ---------------------------------------------------------------------------
# 10-12: Propagation, Threshold Filtering & Temporal Metrics
# ---------------------------------------------------------------------------


def test_perturbation_analysis_deltas_and_threshold():
    """Verify delta calculation and threshold-based model-affected classification."""
    g = nx.DiGraph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    # A: +0.6, B: +0.3, C: +0.02
    mock_sim = _create_mock_simulation_result(
        node_ids=["A", "B", "C"],
        target_ids=["A"],
        baseline_val=0.2,
        perturbed_map={"A": 0.8, "B": 0.5, "C": 0.22},
    )

    # Threshold 0.05: A (0.6) and B (0.3) exceed, C (0.02) does not
    pert_analysis = compute_perturbation_analysis(g, mock_sim, threshold=0.05)
    assert pert_analysis.threshold == 0.05
    assert pert_analysis.network_summary.model_affected_neuron_count == 2
    assert pert_analysis.network_summary.model_affected_neuron_fraction == pytest.approx(2 / 3, abs=1e-3)
    assert pert_analysis.network_summary.max_absolute_activity_change == 0.6

    by_id = {n.neuron_id: n for n in pert_analysis.affected_neurons}
    assert by_id["A"].exceeds_threshold is True
    assert by_id["B"].exceeds_threshold is True
    assert by_id["C"].exceeds_threshold is False
    assert by_id["A"].is_target is True
    assert by_id["B"].is_target is False


def test_temporal_metrics_auc_and_time_to_threshold():
    """Verify numerical trapezoidal integration (AUC) and time-to-threshold."""
    s0 = SimulationState(time=0.0, neuron_activity={"A": 0.2})
    s1 = SimulationState(time=1.0, neuron_activity={"A": 0.6})
    s2 = SimulationState(time=2.0, neuron_activity={"A": 0.8})

    b0 = SimulationState(time=0.0, neuron_activity={"A": 0.2})
    b1 = SimulationState(time=1.0, neuron_activity={"A": 0.2})
    b2 = SimulationState(time=2.0, neuron_activity={"A": 0.2})

    temp = compute_temporal_metrics(
        time_series=[s0, s1, s2],
        baseline_time_series=[b0, b1, b2],
        threshold=0.3,
    )

    assert len(temp) == 1
    t = temp[0]
    assert t.neuron_id == "A"
    assert t.initial_activity == 0.2
    assert t.final_activity == 0.8
    assert t.max_activity == 0.8
    assert t.min_activity == 0.2
    assert t.peak_absolute_change == 0.6
    assert t.time_of_peak_change == 2.0
    # Trapezoid AUC:
    # [0 to 1]: (0.2 + 0.6)/2 * 1 = 0.4
    # [1 to 2]: (0.6 + 0.8)/2 * 1 = 0.7
    # Total AUC = 1.1
    assert t.area_under_curve == pytest.approx(1.1, abs=1e-3)
    # At t=1.0, |0.6 - 0.2| = 0.4 >= 0.3 threshold
    assert t.time_to_threshold == 1.0


# ---------------------------------------------------------------------------
# 21: Mathematical Sanity Fixture (Section 21 of Spec)
# ---------------------------------------------------------------------------


def test_mathematical_sanity_fixture_a_b_c():
    """
    Validates Section 21 of AGENTS.md / Request:
    Graph: A -> B -> C
    Expected:
    - A has downstream reachability to B and C
    - C has no downstream nodes
    - B lies on the A->C path
    - degree values are deterministic
    - shortest path A->C = 2
    For a perturbed state:
    baseline: A=0.2, B=0.2, C=0.2
    perturbed: A=0.8, B=0.5, C=0.3
    verify:
    ΔA = 0.6, ΔB = 0.3, ΔC = 0.1
    """
    g = nx.DiGraph()
    g.add_edge("A", "B", weight=1.0)
    g.add_edge("B", "C", weight=1.0)

    # Topological validation
    target_res = compute_target_analysis(g, target_neuron_ids=["A", "C"], max_hops=3)
    by_target = {t.target_neuron_id: t for t in target_res}

    # A reachability
    assert by_target["A"].reachability_by_hop[1] == ["B"]
    assert by_target["A"].reachability_by_hop[2] == ["C"]
    assert by_target["A"].shortest_path_lengths_downstream["C"] == 2

    # C has no downstream nodes
    assert by_target["C"].downstream_neuron_count == 0
    assert by_target["C"].reachability_counts[1] == 0

    # B lies on A->C path
    path = nx.shortest_path(g, "A", "C")
    assert path == ["A", "B", "C"]

    # Perturbation delta validation
    mock_sim = _create_mock_simulation_result(
        node_ids=["A", "B", "C"],
        target_ids=["A"],
        baseline_val=0.2,
        perturbed_map={"A": 0.8, "B": 0.5, "C": 0.3},
    )

    pert_analysis = compute_perturbation_analysis(g, mock_sim, threshold=0.05)
    by_nid = {n.neuron_id: n for n in pert_analysis.affected_neurons}

    assert by_nid["A"].delta_activity == pytest.approx(0.6, abs=1e-4)
    assert by_nid["B"].delta_activity == pytest.approx(0.3, abs=1e-4)
    assert by_nid["C"].delta_activity == pytest.approx(0.1, abs=1e-4)


# ---------------------------------------------------------------------------
# Engine Safeguards & Provenance
# ---------------------------------------------------------------------------


def test_engine_exceeds_node_limit():
    """Verify engine raises ValueError if graph exceeds MAX_ANALYSIS_NODES."""
    g = nx.DiGraph()
    for i in range(MAX_ANALYSIS_NODES + 10):
        g.add_node(f"n_{i}")

    mock_sim = _create_mock_simulation_result()
    engine = NetworkAnalysisEngine()

    with pytest.raises(ValueError, match="exceeds analysis limit"):
        engine.analyze(g, mock_sim)


def test_engine_provenance_preservation():
    """Verify that provider, dataset name, version, and synthetic flags are preserved."""
    g = nx.DiGraph()
    g.add_edge("1", "2")

    mock_sim = _create_mock_simulation_result(
        sim_id="sim_prov_test",
        node_ids=["1", "2"],
        target_ids=["1"],
        is_synthetic=False,
    )
    mock_sim.provenance.connectome_provider = "MaleCNS-v1.0"
    mock_sim.provenance.dataset_name = "janelia_male_cns"
    mock_sim.provenance.dataset_version = "v1.0"

    engine = NetworkAnalysisEngine()
    result = engine.analyze(g, mock_sim, threshold=0.08, max_hops=4)

    assert result.simulation_id == "sim_prov_test"
    assert result.provenance.connectome_provider == "MaleCNS-v1.0"
    assert result.provenance.dataset_name == "janelia_male_cns"
    assert result.provenance.dataset_version == "v1.0"
    assert result.provenance.is_synthetic is False
    assert result.provenance.threshold == 0.08
    assert result.provenance.max_hops == 4
    assert result.provenance.neuron_count == 2


def test_engine_subgraph_response_input():
    """Verify engine accepts SubgraphResponse object directly."""
    neurons = [
        Neuron(neuron_id="101", cell_type="TypeA", region="Protocerebrum", x=1.0, y=2.0, z=3.0),
        Neuron(neuron_id="102", cell_type="TypeB", region="Protocerebrum", x=4.0, y=5.0, z=6.0),
    ]
    conns = [Connection(source_neuron="101", target_neuron="102", weight=2.5)]
    subgraph = SubgraphResponse(neurons=neurons, connections=conns)

    mock_sim = _create_mock_simulation_result(
        sim_id="subgraph_resp_sim",
        node_ids=["101", "102"],
        target_ids=["101"],
    )

    engine = NetworkAnalysisEngine()
    result = engine.analyze(subgraph, mock_sim)
    assert result.network_metrics.neuron_count == 2
    assert result.network_metrics.connection_count == 1
    assert result.network_metrics.mean_in_degree == 0.5


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


def test_api_network_analysis_post_and_get():
    """Verify POST /analysis/network and GET /analysis/network/{sim_id}."""
    g = nx.DiGraph()
    g.add_edge("10", "20")

    mock_sim = _create_mock_simulation_result(
        sim_id="sim_api_test",
        node_ids=["10", "20"],
        target_ids=["10"],
    )
    _store_simulation(mock_sim, graph=g)

    # 1. POST /analysis/network
    payload = {
        "simulation_id": "sim_api_test",
        "threshold": 0.1,
        "max_hops": 2,
    }
    resp = client.post("/analysis/network", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulation_id"] == "sim_api_test"
    assert data["network_metrics"]["neuron_count"] == 2
    assert data["network_metrics"]["connection_count"] == 1
    assert len(data["centrality"]) == 2
    assert len(data["target_analysis"]) == 1
    assert data["provenance"]["threshold"] == 0.1

    # 2. GET /analysis/network/{sim_id}
    get_resp = client.get("/analysis/network/sim_api_test?threshold=0.05&max_hops=3")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["simulation_id"] == "sim_api_test"
    assert get_data["provenance"]["threshold"] == 0.05


def test_api_network_analysis_simulation_not_found():
    """Verify 404 is returned when simulation ID does not exist."""
    resp = client.post("/analysis/network", json={"simulation_id": "nonexistent_sim"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_network_analysis_validation_error():
    """Verify validation on threshold and hop constraints."""
    resp = client.post("/analysis/network", json={"simulation_id": "sim_1", "threshold": -0.5})
    assert resp.status_code == 422

    resp2 = client.post("/analysis/network", json={"simulation_id": "sim_1", "max_hops": 20})
    assert resp2.status_code == 422
