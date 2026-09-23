from fastapi.testclient import TestClient
from app.main import app
from app.connectome.synthetic import SyntheticConnectomeProvider

client = TestClient(app)

def test_synthetic_provider_determinism():
    """Test that two providers initialized with the same seed produce the same graph."""
    provider1 = SyntheticConnectomeProvider(seed=123, num_neurons=50, edge_probability=0.1)
    provider2 = SyntheticConnectomeProvider(seed=123, num_neurons=50, edge_probability=0.1)
    
    assert provider1.get_metadata().neuron_count == provider2.get_metadata().neuron_count
    assert provider1.get_metadata().connection_count == provider2.get_metadata().connection_count
    
    # Check that a random neuron is identical
    n1 = provider1.get_neuron("syn_neuron_0")
    n2 = provider2.get_neuron("syn_neuron_0")
    assert n1 is not None
    assert n2 is not None
    assert n1.cell_type == n2.cell_type
    assert n1.region == n2.region

def test_provider_queries():
    provider = SyntheticConnectomeProvider(seed=42, num_neurons=50, edge_probability=0.1)
    
    # test get_neuron
    neuron = provider.get_neuron("syn_neuron_5")
    assert neuron is not None
    assert neuron.neuron_id == "syn_neuron_5"
    
    # test get_neurons_by_cell_type
    cell_type_neurons = provider.get_neurons_by_cell_type(neuron.cell_type)
    assert len(cell_type_neurons) > 0
    assert all(n.cell_type == neuron.cell_type for n in cell_type_neurons)
    
    # test get_neurons_by_region
    region_neurons = provider.get_neurons_by_region(neuron.region)
    assert len(region_neurons) > 0
    assert all(n.region == neuron.region for n in region_neurons)
    
    # test get_connections
    connections = provider.get_connections("syn_neuron_5")
    assert isinstance(connections, list)
    
    # test extract_subgraph
    subgraph = provider.extract_subgraph(["syn_neuron_1", "syn_neuron_2", "syn_neuron_3"])
    assert len(subgraph.neurons) == 3
    assert all(n.neuron_id in ["syn_neuron_1", "syn_neuron_2", "syn_neuron_3"] for n in subgraph.neurons)

def test_api_connectome_info():
    response = client.get("/connectome/info")
    assert response.status_code == 200
    data = response.json()
    assert data["is_synthetic"] is True
    assert data["provider_type"] == "SyntheticConnectomeProvider"
    assert data["neuron_count"] == 100

def test_api_connectome_neurons():
    # Use limit=500 to retrieve all 100 synthetic neurons
    # (the API default is limit=50, which is correct for large real datasets)
    response = client.get("/connectome/neurons?limit=500")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100
    
    # test filtering
    if len(data) > 0:
        sample_type = data[0]["cell_type"]
        filter_response = client.get(f"/connectome/neurons?cell_type={sample_type}")
        filter_data = filter_response.json()
        assert len(filter_data) > 0
        assert all(n["cell_type"] == sample_type for n in filter_data)

def test_api_connectome_single_neuron():
    response = client.get("/connectome/neurons/syn_neuron_42")
    assert response.status_code == 200
    data = response.json()
    assert data["neuron_id"] == "syn_neuron_42"
    
    response_404 = client.get("/connectome/neurons/non_existent")
    assert response_404.status_code == 404

def test_api_connectome_neighbors():
    response = client.get("/connectome/neurons/syn_neuron_10/neighbors?hops=1")
    assert response.status_code == 200
    data = response.json()
    assert "neurons" in data
    assert "connections" in data
    # the ego neuron should be in the subgraph
    assert any(n["neuron_id"] == "syn_neuron_10" for n in data["neurons"])

def test_api_connectome_subgraph():
    response = client.post("/connectome/subgraph", json=["syn_neuron_0", "syn_neuron_1"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["neurons"]) == 2
    ids = [n["neuron_id"] for n in data["neurons"]]
    assert "syn_neuron_0" in ids
    assert "syn_neuron_1" in ids
