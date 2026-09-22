from pydantic import BaseModel, Field
from typing import List, Optional

class Neuron(BaseModel):
    neuron_id: str
    cell_type: str
    region: str
    x: float
    y: float
    z: float

class Connection(BaseModel):
    source_neuron: str
    target_neuron: str
    weight: float

class ConnectomeMetadata(BaseModel):
    id: str
    description: str
    neuron_count: int
    connection_count: int
    provider_type: str
    is_synthetic: bool = True

class SubgraphResponse(BaseModel):
    neurons: List[Neuron]
    connections: List[Connection]
