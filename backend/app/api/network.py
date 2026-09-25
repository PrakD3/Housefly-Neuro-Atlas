"""
Network Analysis API endpoints for Drosophila-NeuroAtlas Phase 6.

Routes:
- POST /analysis/network: Run structural and perturbation network analysis on a completed simulation
- GET  /analysis/network/{simulation_id}: Retrieve analysis using default parameters

SCIENTIFIC PRINCIPLE:
Network analysis results describe the computational graph topology and modeled state differences.
They do not indicate biological importance, pharmacological efficacy, or toxicity.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..connectome.factory import get_provider
from ..connectome.real.client import NeuPrintError
from ..models.network import NetworkAnalysisRequest, NetworkAnalysisResult
from ..network.engine import (
    MAX_ANALYSIS_EDGES,
    MAX_ANALYSIS_NODES,
    MAX_PATH_LENGTH,
    NetworkAnalysisEngine,
)
from .simulation import _get_stored_graph, _get_stored_simulation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "/network",
    response_model=NetworkAnalysisResult,
    status_code=status.HTTP_200_OK,
)
def run_network_analysis(request: NetworkAnalysisRequest):
    """
    Execute comprehensive structural and perturbation analysis on a completed simulation.

    Ingests:
    - simulation_id: Must match an active or cached simulation run
    - threshold: Activity delta threshold in [0.0, 1.0] to classify model-affected neurons
    - max_hops: Reachability depth in [1, 10] for target-centered propagation

    Returns:
    - NetworkAnalysisResult containing structural metrics, centralities, target reachability,
      propagation dynamics, and complete provenance.
    """
    sim_result = _get_stored_simulation(request.simulation_id)
    if not sim_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation with ID '{request.simulation_id}' not found.",
        )

    # Retrieve underlying graph from cache or reconstruct via provider
    graph = _get_stored_graph(request.simulation_id)
    if graph is None:
        try:
            neuron_ids = [d.neuron_id for d in sim_result.neuron_deltas]
            provider = get_provider()
            graph = provider.extract_subgraph(neuron_ids)
        except NeuPrintError as exc:
            logger.error("neuPrint error reconstructing graph for analysis: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Connectome provider error: {str(exc)}",
            )
        except Exception as exc:
            logger.error("Failed to reconstruct graph for analysis: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not retrieve graph for simulation '{request.simulation_id}': {str(exc)}",
            )

    engine = NetworkAnalysisEngine()
    try:
        return engine.analyze(
            graph=graph,
            simulation_result=sim_result,
            threshold=request.threshold,
            max_hops=request.max_hops,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Network analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network analysis failed: {str(exc)}",
        )


@router.get(
    "/network/{simulation_id}",
    response_model=NetworkAnalysisResult,
    status_code=status.HTTP_200_OK,
)
def get_network_analysis(
    simulation_id: str,
    threshold: float = Query(0.05, ge=0.0, le=1.0, description="Model-affected activity delta threshold"),
    max_hops: int = Query(3, ge=1, le=10, description="Reachability depth in hops"),
):
    """
    Convenience GET endpoint to run/retrieve network analysis for a simulation with query parameters.
    """
    request = NetworkAnalysisRequest(
        simulation_id=simulation_id,
        threshold=threshold,
        max_hops=max_hops,
    )
    return run_network_analysis(request)
