from pydantic import BaseModel
from typing import List, Optional


class Neuron(BaseModel):
    """
    Internal representation of a single neuron.

    Coordinates (x, y, z) are Optional[float] and may be None when the
    source data does not provide somaLocation.  has_coordinates is the
    canonical gate — downstream code MUST check this before using x/y/z.

    IMPORTANT: coordinates are NEVER defaulted to (0, 0, 0) or any other
    sentinel value.  None means the data is absent; it must never be
    fabricated or inferred.
    """
    neuron_id: str
    cell_type: str
    region: str

    # Spatial position — nullable.  None when somaLocation absent in source.
    # has_coordinates=True only when x, y, z are all non-None.
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    has_coordinates: bool = False

    # Optional real-data metadata fields (absent for synthetic neurons)
    neurotransmitter: Optional[str] = None
    status: Optional[str] = None
    instance: Optional[str] = None


class Connection(BaseModel):
    """A directed synaptic connection between two neurons."""
    source_neuron: str
    target_neuron: str
    weight: float


class ConnectomeMetadata(BaseModel):
    """
    Metadata describing the currently active connectome.

    is_synthetic distinguishes test / development data from real biological data.
    When is_synthetic=False the dataset_name and dataset_version fields identify
    the exact biological source so it cannot be confused with synthetic data.
    """
    id: str
    description: str
    neuron_count: int
    connection_count: int
    provider_type: str
    is_synthetic: bool = True

    # Real-data provenance — populated by RealDrosophilaConnectomeProvider only
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    organism: Optional[str] = None
    sex: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


class SubgraphResponse(BaseModel):
    """A subgraph containing a set of neurons and the connections between them."""
    neurons: List[Neuron]
    connections: List[Connection]


class SubgraphProvenance(BaseModel):
    """Provenance metadata for an extracted subgraph."""
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    is_synthetic: bool = True
    query_timestamp: Optional[str] = None


class BoundedSubgraphResponse(SubgraphResponse):
    """
    Bounded subgraph response with server-enforced limits and provenance.
    Guarantees browser-safe payload size for visualization.
    """
    neuron_count: int
    connection_count: int
    was_truncated: bool
    max_neurons_limit: int
    max_connections_limit: int
    query_neuron_id: str
    hops: int
    provenance: Optional[SubgraphProvenance] = None

