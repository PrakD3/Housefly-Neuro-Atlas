import networkx as nx
import random
from typing import List, Optional
from ..models.connectome import Neuron, Connection, ConnectomeMetadata, SubgraphResponse
from .provider import ConnectomeProvider

class SyntheticConnectomeProvider(ConnectomeProvider):
    def __init__(self, seed: int = 42, num_neurons: int = 100, edge_probability: float = 0.05):
        self.seed = seed
        self.num_neurons = num_neurons
        self.edge_probability = edge_probability
        
        self.graph = nx.DiGraph()
        self.neurons_metadata = {}
        self._generate_graph()

    def _generate_graph(self):
        """Generates a deterministic synthetic graph using a fixed random seed."""
        # Use a local random instance for determinism
        rng = random.Random(self.seed)
        
        cell_types = ["Kenyon_Cell", "Projection_Neuron", "Motor_Neuron", "Sensory_Neuron", "Interneuron"]
        regions = ["Mushroom_Body", "Antennal_Lobe", "Optic_Lobe", "Ventral_Nerve_Cord", "Central_Complex"]
        
        # Generate nodes (neurons)
        for i in range(self.num_neurons):
            neuron_id = f"syn_neuron_{i}"
            
            neuron = Neuron(
                neuron_id=neuron_id,
                cell_type=rng.choice(cell_types),
                region=rng.choice(regions),
                x=rng.uniform(-100.0, 100.0),
                y=rng.uniform(-100.0, 100.0),
                z=rng.uniform(-100.0, 100.0)
            )
            
            self.graph.add_node(neuron_id)
            self.neurons_metadata[neuron_id] = neuron
            
        # Generate edges (connections) deterministically
        # ER graph generation manually to use our local rng
        for u in self.graph.nodes():
            for v in self.graph.nodes():
                if u != v:
                    if rng.random() < self.edge_probability:
                        weight = rng.uniform(0.1, 5.0)
                        self.graph.add_edge(u, v, weight=weight)
                        
    def get_metadata(self) -> ConnectomeMetadata:
        return ConnectomeMetadata(
            id=f"synthetic_er_{self.num_neurons}_{self.edge_probability}",
            description="Synthetic Drosophila Connectome (Random ER Graph for Development)",
            neuron_count=self.graph.number_of_nodes(),
            connection_count=self.graph.number_of_edges(),
            provider_type="SyntheticConnectomeProvider",
            is_synthetic=True
        )

    def get_neuron(self, neuron_id: str) -> Optional[Neuron]:
        return self.neurons_metadata.get(neuron_id)

    def get_neurons_by_cell_type(self, cell_type: str) -> List[Neuron]:
        return [n for n in self.neurons_metadata.values() if n.cell_type == cell_type]

    def get_neurons_by_region(self, region: str) -> List[Neuron]:
        return [n for n in self.neurons_metadata.values() if n.region == region]

    def get_neighbors(self, neuron_id: str, hops: int = 1) -> SubgraphResponse:
        if neuron_id not in self.graph:
            return SubgraphResponse(neurons=[], connections=[])
            
        # Extract ego graph up to 'hops' radius
        # Note: nx.ego_graph with undirected=False gets both predecessors and successors if we use ego_graph
        # For directed graphs, if we want downstream and upstream, we might need undirected=True to traverse both directions,
        # but extract the subgraph from the original directed graph.
        
        # We will use undirected=True to get nodes within N hops regardless of direction
        undirected_ego = nx.ego_graph(self.graph.to_undirected(), neuron_id, radius=hops)
        
        # The subgraph induced by these nodes in the original directed graph
        induced_subgraph = self.graph.subgraph(undirected_ego.nodes())
        
        return self._extract_from_nx_graph(induced_subgraph)

    def get_connections(self, neuron_id: str) -> List[Connection]:
        if neuron_id not in self.graph:
            return []
            
        connections = []
        
        # Outgoing edges
        for _, target, data in self.graph.out_edges(neuron_id, data=True):
            connections.append(Connection(
                source_neuron=neuron_id,
                target_neuron=target,
                weight=data.get('weight', 1.0)
            ))
            
        # Incoming edges
        for source, _, data in self.graph.in_edges(neuron_id, data=True):
            connections.append(Connection(
                source_neuron=source,
                target_neuron=neuron_id,
                weight=data.get('weight', 1.0)
            ))
            
        return connections

    def extract_subgraph(self, neuron_ids: List[str]) -> SubgraphResponse:
        # Filter to only neurons that exist in the graph
        valid_nodes = [nid for nid in neuron_ids if nid in self.graph]
        
        induced_subgraph = self.graph.subgraph(valid_nodes)
        return self._extract_from_nx_graph(induced_subgraph)
        
    def _extract_from_nx_graph(self, nx_graph: nx.DiGraph) -> SubgraphResponse:
        neurons = [self.neurons_metadata[nid] for nid in nx_graph.nodes()]
        
        connections = []
        for u, v, data in nx_graph.edges(data=True):
            connections.append(Connection(
                source_neuron=u,
                target_neuron=v,
                weight=data.get('weight', 1.0)
            ))
            
        return SubgraphResponse(neurons=neurons, connections=connections)
