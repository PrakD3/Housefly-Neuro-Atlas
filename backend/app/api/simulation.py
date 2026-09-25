"""
Simulation API endpoints for Drosophila-NeuroAtlas Phase 5.

Routes:
- POST /simulations: Run baseline & perturbed simulation on a bounded subgraph
- GET  /simulations/{simulation_id}: Retrieve simulation results by ID
- GET  /simulations/{simulation_id}/results: Retrieve simulation results
- POST /simulations/{simulation_id}/run: Run/re-run simulation with given parameters

Safety & limits:
- Max 500 neurons per simulation run
- Max 20 perturbations per request
- Max 50.0 seconds duration
- In-memory bounded cache for recent simulation results (capacity: 50)
"""
from collections import OrderedDict
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..connectome.factory import get_provider
from ..connectome.real.client import NeuPrintError
from ..models.connectome import SubgraphResponse
from ..models.simulation import (
    NeuralPerturbation,
    SimulationConfig,
    SimulationResult,
    SimulationRunRequest,
)
from ..simulation.engine import (
    MAX_PERTURBATIONS,
    MAX_SIMULATION_NEURONS,
    SimulationEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulations"])

# In-memory bounded cache for recent simulations
_SIMULATION_CACHE_CAPACITY = 50
_simulation_cache: OrderedDict[str, SimulationResult] = OrderedDict()
_graph_cache: OrderedDict[str, any] = OrderedDict()


def _store_simulation(result: SimulationResult, graph: Optional[any] = None) -> None:
    """Store result and optional underlying graph in bounded LRU cache."""
    if len(_simulation_cache) >= _SIMULATION_CACHE_CAPACITY:
        oldest_id, _ = _simulation_cache.popitem(last=False)
        _graph_cache.pop(oldest_id, None)
    _simulation_cache[result.simulation_id] = result
    if graph is not None:
        _graph_cache[result.simulation_id] = graph


def _get_stored_simulation(sim_id: str) -> Optional[SimulationResult]:
    """Retrieve result from cache."""
    return _simulation_cache.get(sim_id)


def _get_stored_graph(sim_id: str) -> Optional[any]:
    """Retrieve graph associated with simulation from cache."""
    return _graph_cache.get(sim_id)


def clear_simulation_cache() -> None:
    """Clear simulation cache (useful for testing)."""
    _simulation_cache.clear()
    _graph_cache.clear()


@router.post("", response_model=SimulationResult, status_code=status.HTTP_201_CREATED)
def create_and_run_simulation(request: SimulationRunRequest):
    """
    Initiate and run a computational neural perturbation simulation.

    Accepts target subgraph specification via:
    - focal_neuron_id + hops (fetches bounded neighborhood from active provider)
    - neuron_ids (extracts subgraph from active provider)
    - or defaults to active synthetic graph (capped at 500 neurons)

    Runs both baseline (unperturbed) and perturbed simulations to produce
    comprehensive activity deltas, multi-hop propagation metrics, and provenance.
    """
    if len(request.perturbations) > MAX_PERTURBATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded maximum allowed perturbations (limit: {MAX_PERTURBATIONS}, requested: {len(request.perturbations)}).",
        )

    provider = get_provider()
    metadata = provider.get_metadata()

    try:
        # Extract target subgraph
        if request.focal_neuron_id:
            subgraph_resp = provider.get_neighbors(
                request.focal_neuron_id, hops=request.hops
            )
        elif request.neuron_ids:
            subgraph_resp = provider.extract_subgraph(request.neuron_ids)
        else:
            if not metadata.is_synthetic:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Real connectome simulation requires specifying 'focal_neuron_id' or 'neuron_ids' to extract a bounded subgraph.",
                )
            # Synthetic provider fallback: extract connected subgraph of up to 100 neurons
            all_neurons = provider.get_neurons_by_cell_type("Sensory") + provider.get_neurons_by_cell_type("Interneuron")
            sample_ids = [n.neuron_id for n in all_neurons[:50]]
            subgraph_resp = provider.extract_subgraph(sample_ids)

    except HTTPException:
        raise
    except NeuPrintError as exc:
        logger.error("neuPrint error fetching simulation subgraph: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Real connectome provider error: {str(exc)}",
        )
    except Exception as exc:
        logger.error("Error retrieving subgraph for simulation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract subgraph: {str(exc)}",
        )

    if not subgraph_resp.neurons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The extracted subgraph contains no neurons. Cannot run simulation.",
        )

    if len(subgraph_resp.neurons) > MAX_SIMULATION_NEURONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Simulation exceeds maximum allowed size of {MAX_SIMULATION_NEURONS} neurons "
                f"(extracted: {len(subgraph_resp.neurons)}). Please reduce hops or neuron list."
            ),
        )

    # Initialize engine
    config = request.config or SimulationConfig()
    engine = SimulationEngine(config=config)

    meta_dict = {
        "provider_type": metadata.provider_type,
        "is_synthetic": metadata.is_synthetic,
        "dataset_name": metadata.dataset_name if not metadata.is_synthetic else "synthetic",
        "dataset_version": metadata.dataset_version if not metadata.is_synthetic else None,
    }

    try:
        engine.initialize(
            graph=subgraph_resp,
            perturbations=request.perturbations,
            config=config,
            metadata_source=meta_dict,
        )
        result = engine.run_comparison()
        _store_simulation(result, graph=engine.graph)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected simulation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation run failed: {str(exc)}",
        )


@router.get("/{simulation_id}", response_model=SimulationResult)
def get_simulation(simulation_id: str):
    """Retrieve the results and provenance of a previous simulation run."""
    result = _get_stored_simulation(simulation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation with ID '{simulation_id}' not found.",
        )
    return result


@router.get("/{simulation_id}/results", response_model=SimulationResult)
def get_simulation_results(simulation_id: str):
    """Alias to retrieve simulation results."""
    return get_simulation(simulation_id)


@router.post("/{simulation_id}/run", response_model=SimulationResult)
def rerun_simulation(
    simulation_id: str,
    duration: Optional[float] = Query(None, ge=0.1, le=50.0),
):
    """Re-run an existing simulation with an optional duration override."""
    existing = _get_stored_simulation(simulation_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation with ID '{simulation_id}' not found.",
        )

    # Extract original neuron IDs and re-run
    neuron_ids = [d.neuron_id for d in existing.neuron_deltas]
    provider = get_provider()
    subgraph_resp = provider.extract_subgraph(neuron_ids)

    config = existing.config.model_copy()
    if duration is not None:
        config.duration = duration

    engine = SimulationEngine(config=config)
    meta_dict = {
        "provider_type": existing.provenance.connectome_provider,
        "is_synthetic": existing.provenance.is_synthetic,
        "dataset_name": existing.provenance.dataset_name,
        "dataset_version": existing.provenance.dataset_version,
    }

    engine.initialize(
        graph=subgraph_resp,
        perturbations=existing.provenance.perturbations,
        config=config,
        metadata_source=meta_dict,
    )
    result = engine.run_comparison(duration=duration)
    _store_simulation(result, graph=engine.graph)
    return result
