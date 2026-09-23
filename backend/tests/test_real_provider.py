"""
Tests for the RealDrosophilaConnectomeProvider and related components.

ALL tests use mocked HTTP responses — no real network calls are made.
Tests must pass without any NEUPRINT_TOKEN set.

Fixture data is based on the documented neuPrint /api/custom/custom
response format (columns + data rows).  It is clearly labelled as test
fixture data and does NOT represent real biological values.

neuPrint API reference:
  https://neuprint.janelia.org/api/help/swagger.yaml
  Endpoint: POST /api/custom/custom
  Response: { "columns": [...], "data": [[...], ...] }
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from app.connectome.real.client import (
    NeuPrintAuthenticationError,
    NeuPrintClient,
    NeuPrintConnectionError,
    NeuPrintResponseError,
)
from app.connectome.real.cache import LRUCache
from app.connectome.real.models import NeuPrintNeuronRecord
from app.connectome.real.provider import RealDrosophilaConnectomeProvider
from app.connectome.real.provenance import MALE_CNS_V1_PROVENANCE
from app.connectome.factory import get_provider, reset_provider
from app.connectome.synthetic import SyntheticConnectomeProvider

# ---------------------------------------------------------------------------
# Test fixtures — representative neuPrint response shapes
# These are TEST FIXTURES only.  Body IDs and values are illustrative.
# They reflect the documented neuPrint API response format, not real biology.
# ---------------------------------------------------------------------------

FIXTURE_NEURON_RESPONSE = {
    "columns": [
        "bodyId", "type", "instance", "superClass",
        "status", "predictedNt", "somaLocation"
    ],
    "data": [
        # Neuron with somaLocation (has_coordinates=True)
        [720575940614131, "DNge104", "DNge104_R", "descending",
         "Traced", "acetylcholine", [15000, 20000, 18000]],
        # Neuron without somaLocation (has_coordinates=False)
        [720575940614132, "T4a", "T4a_L", "visual",
         "Traced", "glutamate", None],
    ]
}

# Single-neuron fixture: neuron WITH coordinates
FIXTURE_NEURON_WITH_SOMA = {
    "columns": [
        "bodyId", "type", "instance", "superClass",
        "status", "predictedNt", "somaLocation"
    ],
    "data": [
        [100001, "DNge104", "DNge104_R", "descending",
         "Traced", "acetylcholine", [15000.0, 20000.0, 18000.0]],
    ]
}

# Single-neuron fixture: neuron WITHOUT coordinates (somaLocation is None)
FIXTURE_NEURON_WITHOUT_SOMA = {
    "columns": [
        "bodyId", "type", "instance", "superClass",
        "status", "predictedNt", "somaLocation"
    ],
    "data": [
        [100002, "T4a", "T4a_L", "visual",
         "Traced", "glutamate", None],
    ]
}

# Two-row fixture used by cell-type, region, and subgraph tests
FIXTURE_NEURON_RESPONSE_CLEAN = {
    "columns": [
        "bodyId", "type", "instance", "superClass",
        "status", "predictedNt", "somaLocation"
    ],
    "data": [
        [100001, "DNge104", "DNge104_R", "descending",
         "Traced", "acetylcholine", [15000.0, 20000.0, 18000.0]],
        [100002, "T4a", "T4a_L", "visual",
         "Traced", "glutamate", None],
    ]
}

FIXTURE_CONNECTION_RESPONSE = {
    "columns": ["source", "target", "weight"],
    "data": [
        [100001, 100002, 42],
        [100003, 100001, 17],
    ]
}

FIXTURE_EMPTY_RESPONSE = {
    "columns": ["bodyId", "type", "instance", "superClass",
                "status", "predictedNt", "somaLocation"],
    "data": []
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider(mock_query_fn=None):
    """Create a RealDrosophilaConnectomeProvider with a mocked client."""
    client = MagicMock(spec=NeuPrintClient)
    if mock_query_fn is not None:
        client.query_cypher.side_effect = mock_query_fn
    return RealDrosophilaConnectomeProvider(client=client)


# ---------------------------------------------------------------------------
# 1. Provider initialization
# ---------------------------------------------------------------------------

class TestProviderInitialization:
    def test_provider_creation_succeeds_with_mock_client(self):
        client = MagicMock(spec=NeuPrintClient)
        provider = RealDrosophilaConnectomeProvider(client=client)
        assert provider is not None

    def test_provider_type_is_real(self):
        client = MagicMock(spec=NeuPrintClient)
        provider = RealDrosophilaConnectomeProvider(client=client)
        meta = provider.get_metadata()
        assert meta.provider_type == "RealDrosophilaConnectomeProvider"

    def test_is_synthetic_false(self):
        client = MagicMock(spec=NeuPrintClient)
        provider = RealDrosophilaConnectomeProvider(client=client)
        meta = provider.get_metadata()
        assert meta.is_synthetic is False


# ---------------------------------------------------------------------------
# 2. Metadata normalization
# ---------------------------------------------------------------------------

class TestMetadataNormalization:
    def test_metadata_contains_dataset_name(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert meta.dataset_name == "Drosophila Male CNS"

    def test_metadata_contains_dataset_version(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert meta.dataset_version == "v1.0"

    def test_metadata_contains_organism(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert "Drosophila" in meta.organism

    def test_metadata_contains_sex(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert meta.sex == "male"

    def test_metadata_source_url(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert "neuprint.janelia.org" in meta.source_url

    def test_metadata_license(self):
        provider = _make_provider()
        meta = provider.get_metadata()
        assert meta.license == "CC-BY 4.0"


# ---------------------------------------------------------------------------
# 3. Neuron normalization
# ---------------------------------------------------------------------------

class TestNeuronNormalization:
    def test_neuron_with_soma_has_coordinates(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100001")
        assert neuron is not None
        assert neuron.has_coordinates is True
        assert neuron.x == 15000.0
        assert neuron.y == 20000.0
        assert neuron.z == 18000.0

    def test_neuron_without_soma_has_no_coordinates(self):
        """
        CRITICAL: neurons with missing somaLocation must have None coords,
        not (0, 0, 0) or any other sentinel value.
        The mock returns ONLY the no-soma neuron so the provider correctly
        resolves it as the first (and only) result.
        """
        client = MagicMock(spec=NeuPrintClient)
        # Return ONLY the neuron without somaLocation
        client.query_cypher.return_value = FIXTURE_NEURON_WITHOUT_SOMA
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100002")
        assert neuron is not None
        assert neuron.has_coordinates is False
        assert neuron.x is None
        assert neuron.y is None
        assert neuron.z is None

    def test_neuron_coordinates_never_zero_when_absent(self):
        """
        Coordinates must be None, never (0, 0, 0) when somaLocation is missing.
        Uses the single-row no-soma fixture to ensure we are testing the correct neuron.
        """
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_WITHOUT_SOMA
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100002")
        assert neuron is not None
        assert neuron.x is None, "x must be None, not 0.0 or any other value"
        assert neuron.y is None, "y must be None, not 0.0 or any other value"
        assert neuron.z is None, "z must be None, not 0.0 or any other value"

    def test_neuron_cell_type_from_type_field(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100001")
        assert neuron is not None
        assert neuron.cell_type == "DNge104"

    def test_neuron_neurotransmitter_preserved(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100001")
        assert neuron is not None
        assert neuron.neurotransmitter == "acetylcholine"

    def test_neuron_id_is_string(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neuron = provider.get_neuron("100001")
        assert neuron is not None
        assert isinstance(neuron.neuron_id, str)

    def test_missing_neuron_returns_none(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_EMPTY_RESPONSE
        provider = RealDrosophilaConnectomeProvider(client=client)

        result = provider.get_neuron("999999999")
        assert result is None


# ---------------------------------------------------------------------------
# 4. Connection normalization
# ---------------------------------------------------------------------------

class TestConnectionNormalization:
    def test_connections_source_and_target_are_strings(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_CONNECTION_RESPONSE
        provider = RealDrosophilaConnectomeProvider(client=client)

        conns = provider.get_connections("100001")
        assert len(conns) > 0
        for c in conns:
            assert isinstance(c.source_neuron, str)
            assert isinstance(c.target_neuron, str)

    def test_connection_weight_is_float(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_CONNECTION_RESPONSE
        provider = RealDrosophilaConnectomeProvider(client=client)

        conns = provider.get_connections("100001")
        for c in conns:
            assert isinstance(c.weight, float)

    def test_empty_connections(self):
        client = MagicMock(spec=NeuPrintClient)
        empty_conn = {"columns": ["source", "target", "weight"], "data": []}
        client.query_cypher.return_value = empty_conn
        provider = RealDrosophilaConnectomeProvider(client=client)

        conns = provider.get_connections("100001")
        assert conns == []


# ---------------------------------------------------------------------------
# 5. Cell-type lookup
# ---------------------------------------------------------------------------

class TestCellTypeLookup:
    def test_cell_type_lookup_returns_neurons(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neurons = provider.get_neurons_by_cell_type("DNge104")
        assert len(neurons) > 0

    def test_cell_type_empty_result(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_EMPTY_RESPONSE
        provider = RealDrosophilaConnectomeProvider(client=client)

        neurons = provider.get_neurons_by_cell_type("nonexistent_type")
        assert neurons == []


# ---------------------------------------------------------------------------
# 6. Region lookup
# ---------------------------------------------------------------------------

class TestRegionLookup:
    def test_region_lookup_returns_neurons(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neurons = provider.get_neurons_by_region("AL(R)")
        assert len(neurons) > 0

    def test_region_override_applied(self):
        """Neurons returned by region query should report that region."""
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        neurons = provider.get_neurons_by_region("AL(R)")
        for n in neurons:
            assert n.region == "AL(R)"


# ---------------------------------------------------------------------------
# 7. Neighbor lookup
# ---------------------------------------------------------------------------

class TestNeighborLookup:
    def test_neighbors_include_central_neuron(self):
        client = MagicMock(spec=NeuPrintClient)
        # First call: get_connections (returns connections)
        # Subsequent calls: get_neuron for central + neighbors
        client.query_cypher.side_effect = [
            FIXTURE_CONNECTION_RESPONSE,          # get_connections
            FIXTURE_NEURON_RESPONSE_CLEAN,        # get_neuron(100001)
            FIXTURE_NEURON_RESPONSE_CLEAN,        # get_neuron(100002)
            FIXTURE_NEURON_RESPONSE_CLEAN,        # get_neuron(100003)
        ]
        provider = RealDrosophilaConnectomeProvider(client=client)

        result = provider.get_neighbors("100001", hops=1)
        neuron_ids = [n.neuron_id for n in result.neurons]
        assert "100001" in neuron_ids

    def test_neighbors_returns_subgraph_response(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_CONNECTION_RESPONSE
        provider = RealDrosophilaConnectomeProvider(client=client)

        from app.models.connectome import SubgraphResponse
        result = provider.get_neighbors("100001", hops=1)
        assert isinstance(result, SubgraphResponse)


# ---------------------------------------------------------------------------
# 8. Subgraph extraction
# ---------------------------------------------------------------------------

class TestSubgraphExtraction:
    def test_subgraph_returns_subgraph_response(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN

        from app.models.connectome import SubgraphResponse
        provider = RealDrosophilaConnectomeProvider(client=client)
        result = provider.extract_subgraph(["100001", "100002"])
        assert isinstance(result, SubgraphResponse)

    def test_empty_subgraph_request(self):
        provider = _make_provider()
        result = provider.extract_subgraph([])
        assert result.neurons == []
        assert result.connections == []


# ---------------------------------------------------------------------------
# 9. Provider switching via env var
# ---------------------------------------------------------------------------

class TestProviderSwitching:
    def test_synthetic_provider_selected_by_default(self):
        reset_provider()
        with patch.dict(os.environ, {"CONNECTOME_PROVIDER": "synthetic"}):
            provider = get_provider()
            assert isinstance(provider, SyntheticConnectomeProvider)
        reset_provider()

    def test_unknown_mode_falls_back_to_synthetic(self):
        reset_provider()
        with patch.dict(os.environ, {"CONNECTOME_PROVIDER": "invalid_mode"}):
            provider = get_provider()
            assert isinstance(provider, SyntheticConnectomeProvider)
        reset_provider()

    def test_real_mode_raises_auth_error_without_token(self):
        reset_provider()
        with patch.dict(os.environ, {
            "CONNECTOME_PROVIDER": "real",
            "NEUPRINT_TOKEN": "",
        }):
            with pytest.raises(NeuPrintAuthenticationError):
                get_provider()
        reset_provider()


# ---------------------------------------------------------------------------
# 10. Authentication failure handling
# ---------------------------------------------------------------------------

class TestAuthenticationFailure:
    def test_auth_error_propagated_from_client(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.side_effect = NeuPrintAuthenticationError("bad token")
        provider = RealDrosophilaConnectomeProvider(client=client)

        with pytest.raises(NeuPrintAuthenticationError):
            provider.get_neuron("100001")


# ---------------------------------------------------------------------------
# 11. Network failure handling
# ---------------------------------------------------------------------------

class TestNetworkFailure:
    def test_connection_error_propagated(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.side_effect = NeuPrintConnectionError("timeout")
        provider = RealDrosophilaConnectomeProvider(client=client)

        with pytest.raises(NeuPrintConnectionError):
            provider.get_neuron("100001")

    def test_response_error_propagated(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.side_effect = NeuPrintResponseError("bad JSON")
        provider = RealDrosophilaConnectomeProvider(client=client)

        with pytest.raises(NeuPrintResponseError):
            provider.get_connections("100001")


# ---------------------------------------------------------------------------
# 12. Cache behavior
# ---------------------------------------------------------------------------

class TestCacheBehavior:
    def test_neuron_cache_hit_avoids_second_http_call(self):
        client = MagicMock(spec=NeuPrintClient)
        client.query_cypher.return_value = FIXTURE_NEURON_RESPONSE_CLEAN
        provider = RealDrosophilaConnectomeProvider(client=client)

        # First call — should query
        n1 = provider.get_neuron("100001")
        # Second call — should use cache
        n2 = provider.get_neuron("100001")

        assert n1 == n2
        # query_cypher should have been called exactly once
        assert client.query_cypher.call_count == 1

    def test_lru_cache_bounded(self):
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # should evict "a"

        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_cache_clear(self):
        cache = LRUCache()
        cache.set("x", 42)
        cache.clear()
        assert cache.get("x") is None


# ---------------------------------------------------------------------------
# 13. NeuPrintClient — authentication error on empty token
# ---------------------------------------------------------------------------

class TestNeuPrintClientInit:
    def test_empty_token_raises_auth_error(self):
        with pytest.raises(NeuPrintAuthenticationError):
            NeuPrintClient(
                base_url="https://neuprint.janelia.org",
                token="",
                dataset="male-cns:v1.0",
            )

    def test_valid_token_constructs_client(self):
        client = NeuPrintClient(
            base_url="https://neuprint.janelia.org",
            token="test_token_placeholder",
            dataset="male-cns:v1.0",
        )
        assert client is not None
