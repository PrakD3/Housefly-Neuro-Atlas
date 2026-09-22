from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.connectome import Neuron, Connection, ConnectomeMetadata, SubgraphResponse

class ConnectomeProvider(ABC):
    
    @abstractmethod
    def get_metadata(self) -> ConnectomeMetadata:
        """Return metadata about the connectome."""
        pass
        
    @abstractmethod
    def get_neuron(self, neuron_id: str) -> Optional[Neuron]:
        """Retrieve a single neuron by ID."""
        pass

    @abstractmethod
    def get_neurons_by_cell_type(self, cell_type: str) -> List[Neuron]:
        """Retrieve all neurons of a specific cell type."""
        pass

    @abstractmethod
    def get_neurons_by_region(self, region: str) -> List[Neuron]:
        """Retrieve all neurons in a specific region."""
        pass

    @abstractmethod
    def get_neighbors(self, neuron_id: str, hops: int = 1) -> SubgraphResponse:
        """Retrieve the neighborhood subgraph for a given neuron up to `hops` distance."""
        pass

    @abstractmethod
    def get_connections(self, neuron_id: str) -> List[Connection]:
        """Retrieve all directed connections (incoming and outgoing) for a neuron."""
        pass

    @abstractmethod
    def extract_subgraph(self, neuron_ids: List[str]) -> SubgraphResponse:
        """Extract a subgraph containing the specified neurons and any edges between them."""
        pass
