"""
Phase 4 Backend Tests — Real Connectome Visualization Endpoints.

Tests cover:
1. /connectome/neighborhood returns bounded subgraph
2. Neuron count limit enforced
3. Connection count limit enforced
4. was_truncated=True when limits are hit
5. 404 returned when neuron not found
6. Coordinates preserved (None stays None)
7. No fabricated coordinates (has_coordinates correctly set)
8. Provenance fields properly populated
9. /connectome/search returns matching neurons
10. Provider error maps to HTTP 503
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.connectome import (
    BoundedSubgraphResponse,
    Connection,
    ConnectomeMetadata,
    Neuron,
    SubgraphResponse,
)
from app.connectome.real.client import (
    NeuPrintAuthenticationError,
    NeuPrintConnectionError,
    NeuPrintError,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_neighborhood_returns_bounded_subgraph(client):
    """Test 1: /connectome/neighborhood returns a valid BoundedSubgraphResponse."""
    # Using synthetic connectome (default in test)
    # First get a valid neuron ID
    info_resp = client.get("/connectome/info")
    assert info_resp.status_code == 200

    resp = client.get("/connectome/neighborhood?neuron_id=syn_neuron_0&hops=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "neurons" in data
    assert "connections" in data
    assert "neuron_count" in data
    assert "connection_count" in data
    assert data["query_neuron_id"] == "syn_neuron_0"
    assert data["hops"] == 1
    assert data["neuron_count"] == len(data["neurons"])
    assert data["connection_count"] == len(data["connections"])
    assert "provenance" in data
    assert data["provenance"]["is_synthetic"] is True


def test_neighborhood_neuron_count_limit_enforced(client):
    """Test 2: Server-side max_neurons query param restricts returned neurons."""
    resp = client.get("/connectome/neighborhood?neuron_id=syn_neuron_0&hops=1&max_neurons=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["neurons"]) <= 2
    assert data["max_neurons_limit"] == 2
    assert data["neuron_count"] == len(data["neurons"])


def test_neighborhood_connection_count_limit_enforced(client):
    """Test 3: Server-side max_connections restricts returned connections."""
    resp = client.get("/connectome/neighborhood?neuron_id=syn_neuron_0&hops=1&max_connections=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["connections"]) <= 1
    assert data["max_connections_limit"] == 1
    assert data["connection_count"] == len(data["connections"])


def test_neighborhood_was_truncated_flag(client):
    """Test 4: was_truncated is True when limits are hit."""
    resp = client.get("/connectome/neighborhood?neuron_id=syn_neuron_0&hops=1&max_neurons=1")
    assert resp.status_code == 200
    data = resp.json()
    # Since syn_neuron_0 has neighbors, restricting to 1 neuron must set was_truncated=True
    assert data["was_truncated"] is True


def test_neighborhood_404_when_neuron_not_found(client):
    """Test 5: HTTP 404 is returned when the query neuron does not exist."""
    resp = client.get("/connectome/neighborhood?neuron_id=NONEXISTENT_999999&hops=1")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_neighborhood_preserves_none_coordinates(client):
    """Test 6: Real neurons without somaLocation preserve x=None, y=None, z=None."""
    mock_provider = MagicMock()
    mock_neuron_no_coords = Neuron(
        neuron_id="1001",
        cell_type="DNge104",
        region="GNG",
        x=None,
        y=None,
        z=None,
        has_coordinates=False,
    )
    mock_neighbor = Neuron(
        neuron_id="1002",
        cell_type="CB001",
        region="AL",
        x=100.0,
        y=200.0,
        z=300.0,
        has_coordinates=True,
    )
    mock_provider.get_neuron.return_value = mock_neuron_no_coords
    mock_provider.get_neighbors.return_value = SubgraphResponse(
        neurons=[mock_neuron_no_coords, mock_neighbor],
        connections=[Connection(source_neuron="1001", target_neuron="1002", weight=5.0)],
    )
    mock_provider.get_metadata.return_value = ConnectomeMetadata(
        id="male-cns:v1.0",
        description="Real Drosophila connectome",
        neuron_count=100,
        connection_count=200,
        provider_type="RealDrosophilaConnectomeProvider",
        is_synthetic=False,
        dataset_name="male-cns",
        dataset_version="v1.0",
    )

    with patch("app.api.connectome.get_provider", return_value=mock_provider):
        resp = client.get("/connectome/neighborhood?neuron_id=1001&hops=1")
        assert resp.status_code == 200
        data = resp.json()
        central = next(n for n in data["neurons"] if n["neuron_id"] == "1001")
        assert central["x"] is None
        assert central["y"] is None
        assert central["z"] is None
        assert central["has_coordinates"] is False


def test_neighborhood_no_fabricated_coordinates(client):
    """Test 7: No (0,0,0) or fabricated coordinates are generated when coordinates are missing."""
    mock_provider = MagicMock()
    mock_neuron = Neuron(
        neuron_id="2001",
        cell_type="TestType",
        region="EB",
        x=None,
        y=None,
        z=None,
        has_coordinates=False,
    )
    mock_provider.get_neuron.return_value = mock_neuron
    mock_provider.get_neighbors.return_value = SubgraphResponse(
        neurons=[mock_neuron],
        connections=[],
    )
    mock_provider.get_metadata.return_value = ConnectomeMetadata(
        id="male-cns:v1.0",
        description="Real connectome",
        neuron_count=1,
        connection_count=0,
        provider_type="RealDrosophilaConnectomeProvider",
        is_synthetic=False,
    )

    with patch("app.api.connectome.get_provider", return_value=mock_provider):
        resp = client.get("/connectome/neighborhood?neuron_id=2001&hops=1")
        assert resp.status_code == 200
        neuron = resp.json()["neurons"][0]
        # Never fabricated to 0.0
        assert neuron["x"] is not 0.0
        assert neuron["y"] is not 0.0
        assert neuron["z"] is not 0.0
        assert neuron["x"] is None


def test_neighborhood_provenance_fields(client):
    """Test 8: Provenance metadata fields are populated with dataset details and timestamp."""
    mock_provider = MagicMock()
    mock_neuron = Neuron(
        neuron_id="3001",
        cell_type="TypeA",
        region="FB",
        x=10.0,
        y=20.0,
        z=30.0,
        has_coordinates=True,
    )
    mock_provider.get_neuron.return_value = mock_neuron
    mock_provider.get_neighbors.return_value = SubgraphResponse(
        neurons=[mock_neuron],
        connections=[],
    )
    mock_provider.get_metadata.return_value = ConnectomeMetadata(
        id="male-cns:v1.0",
        description="HHMI Janelia MaleCNS v1.0",
        neuron_count=1000,
        connection_count=5000,
        provider_type="RealDrosophilaConnectomeProvider",
        is_synthetic=False,
        dataset_name="male-cns",
        dataset_version="v1.0",
    )

    with patch("app.api.connectome.get_provider", return_value=mock_provider):
        resp = client.get("/connectome/neighborhood?neuron_id=3001&hops=1")
        assert resp.status_code == 200
        prov = resp.json()["provenance"]
        assert prov["dataset_name"] == "male-cns"
        assert prov["dataset_version"] == "v1.0"
        assert prov["is_synthetic"] is False
        assert prov["query_timestamp"] is not None


def test_search_neurons_endpoint(client):
    """Test 9: /connectome/search returns matching neurons."""
    resp = client.get("/connectome/search?query=syn_neuron_0&limit=5")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("syn_neuron_0" in n["neuron_id"] for n in results)


def test_provider_error_maps_to_503(client):
    """Test 10: neuPrint errors in /connectome/neighborhood map to HTTP 503."""
    mock_provider = MagicMock()
    mock_provider.get_neuron.side_effect = NeuPrintAuthenticationError("Auth token invalid")

    with patch("app.api.connectome.get_provider", return_value=mock_provider):
        resp = client.get("/connectome/neighborhood?neuron_id=12345&hops=1")
        assert resp.status_code == 503
        assert "authentication required" in resp.json()["detail"].lower()
