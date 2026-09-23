import networkx as nx
import random
from typing import List, Optional
from ..models.connectome import Neuron, Connection, ConnectomeMetadata, SubgraphResponse
from .provider import ConnectomeProvider

class SyntheticConnectomeProvider(ConnectomeProvider):
    def __init__(self, seed: int = 42, num_neurons: int = 200, edge_probability: float = 0.04):
        self.seed = seed
        self.num_neurons = num_neurons
        self.edge_probability = edge_probability
        
        self.graph = nx.DiGraph()
        self.neurons_metadata = {}
        self._generate_graph()

    def _generate_graph(self):
        """Generates a deterministic synthetic graph with a bilateral brain-like layout."""
        # Use a local random instance for determinism
        rng = random.Random(self.seed)
        
        cell_types = ["Sensory", "Interneuron", "Projection", "Motor", "Modulatory"]
        
        # Spatial regions for a bilateral shape using ellipsoids
        # Center x, y, z and rx, ry, rz
        spatial_regions = [
            {"name": "Left_Lobe", "cx": -12.0, "cy": 0.0, "cz": 0.0, "rx": 7.0, "ry": 9.0, "rz": 6.0},
            {"name": "Right_Lobe", "cx": 12.0, "cy": 0.0, "cz": 0.0, "rx": 7.0, "ry": 9.0, "rz": 6.0},
            {"name": "Central_Bridge", "cx": 0.0, "cy": 0.0, "cz": 0.0, "rx": 5.0, "ry": 4.0, "rz": 3.0}
        ]
        
        # Generate nodes (neurons)
        for i in range(self.num_neurons):
            neuron_id = f"syn_neuron_{i}"
            
            # Choose a spatial region
            s_region = rng.choice(spatial_regions)
            
            # Deterministic cell type assignment based on region
            if s_region["name"] == "Central_Bridge":
                ctype_probs = ["Interneuron", "Interneuron", "Projection", "Modulatory"]
            else:
                ctype_probs = ["Sensory", "Sensory", "Motor", "Projection", "Interneuron", "Modulatory"]
                
            cell_type = rng.choice(ctype_probs)
            
            # Sample point inside an ellipsoid using random numbers
            u = rng.random()
            v = rng.random()
            w = rng.random()
            theta = u * 2.0 * 3.14159
            phi = v * 3.14159
            r = w ** (1.0/3.0)
            import math
            
            x = s_region["cx"] + s_region["rx"] * r * math.sin(phi) * math.cos(theta)
            y = s_region["cy"] + s_region["ry"] * r * math.sin(phi) * math.sin(theta)
            z = s_region["cz"] + s_region["rz"] * r * math.cos(phi)
            
            neuron = Neuron(
                neuron_id=neuron_id,
                cell_type=cell_type,
                region=s_region["name"],
                x=x,
                y=y,
                z=z,
                # Synthetic neurons always have deterministically generated coordinates.
                # has_coordinates MUST be True — the Neuron model defaults to False.
                has_coordinates=True,
            )
            
            self.graph.add_node(neuron_id)
            self.neurons_metadata[neuron_id] = neuron
            
        # Generate edges (connections) deterministically
        for u in self.graph.nodes():
            for v in self.graph.nodes():
                if u != v:
                    u_region = self.neurons_metadata[u].region
                    v_region = self.neurons_metadata[v].region
                    
                    # Higher probability for intra-region, lower for inter-region
                    if u_region == v_region:
                        prob = self.edge_probability * 1.5
                    elif "Central_Bridge" in (u_region, v_region):
                        # Bridge to lobes has medium probability
                        prob = self.edge_probability * 0.8
                    else:
                        # Left lobe directly to Right lobe is rare
                        prob = self.edge_probability * 0.1
                        
                    if rng.random() < prob:
                        weight = rng.uniform(0.1, 5.0)
                        self.graph.add_edge(u, v, weight=weight)
                        
    def get_metadata(self) -> ConnectomeMetadata:
        return ConnectomeMetadata(
            id=f"synthetic_brain_{self.num_neurons}_{self.edge_probability}",
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
