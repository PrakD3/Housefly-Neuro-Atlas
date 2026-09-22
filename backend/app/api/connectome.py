from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models.connectome import Neuron, Connection, ConnectomeMetadata, SubgraphResponse
from ..connectome.synthetic import SyntheticConnectomeProvider

router = APIRouter(prefix="/connectome", tags=["connectome"])

# Instantiate the synthetic provider (later this will be configurable/injectable)
provider = SyntheticConnectomeProvider(seed=42, num_neurons=100, edge_probability=0.05)

@router.get("/info", response_model=ConnectomeMetadata)
def get_connectome_info():
    """Retrieve metadata about the currently loaded connectome."""
    return provider.get_metadata()

@router.get("/neurons", response_model=List[Neuron])
def get_neurons(cell_type: Optional[str] = None, region: Optional[str] = None):
    """Retrieve neurons, optionally filtered by cell_type or region."""
    if cell_type and region:
        # If both are provided, we intersect the results
        neurons_by_type = {n.neuron_id: n for n in provider.get_neurons_by_cell_type(cell_type)}
        neurons_by_region = {n.neuron_id: n for n in provider.get_neurons_by_region(region)}
        common_ids = set(neurons_by_type.keys()) & set(neurons_by_region.keys())
        return [neurons_by_type[nid] for nid in common_ids]
    elif cell_type:
        return provider.get_neurons_by_cell_type(cell_type)
    elif region:
        return provider.get_neurons_by_region(region)
    else:
        # If no filter is provided, maybe return all or limit. We'll return all for the synthetic graph.
        return list(provider.neurons_metadata.values())

@router.get("/neurons/{neuron_id}", response_model=Neuron)
def get_neuron(neuron_id: str):
    """Retrieve a single neuron by ID."""
    neuron = provider.get_neuron(neuron_id)
    if not neuron:
        raise HTTPException(status_code=404, detail="Neuron not found")
    return neuron

@router.get("/neurons/{neuron_id}/neighbors", response_model=SubgraphResponse)
def get_neuron_neighbors(neuron_id: str, hops: int = Query(1, ge=1, le=5)):
    """Retrieve the neighborhood subgraph for a given neuron up to `hops` distance."""
    neuron = provider.get_neuron(neuron_id)
    if not neuron:
        raise HTTPException(status_code=404, detail="Neuron not found")
    return provider.get_neighbors(neuron_id, hops)

@router.post("/subgraph", response_model=SubgraphResponse)
def extract_subgraph(neuron_ids: List[str]):
    """Extract a subgraph containing the specified neurons and any edges between them."""
    return provider.extract_subgraph(neuron_ids)
