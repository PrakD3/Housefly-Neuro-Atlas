"""
Simulation data models for Drosophila-NeuroAtlas Phase 5.

Computational Neural Perturbation Engine:
- normalized neuron activity a in [0.0, 1.0]
- explicit NeuralPerturbation definitions
- baseline vs perturbed comparison models
- network-level metrics
- simulation provenance

IMPORTANT SCIENTIFIC BOUNDARY:
Normalized activity is a COMPUTATIONAL STATE VARIABLE within this graph model.
It does NOT represent experimentally measured neuronal electrophysiology,
membrane potential, action potential firing rates, or biological toxicity.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PerturbationEffect(str, Enum):
    """
    Supported perturbation types.

    Computational equivalence note:
    - In this initial discrete-time graph model, 'activation' and 'excitation'
      are mathematically equivalent (positive shift in target activity).
    - 'inhibition' and 'suppression' are mathematically equivalent
      (negative shift in target activity).
    - 'edge_weight_modification' alters connection weights between target neurons
      and their downstream partners.
    """
    ACTIVATION = "activation"
    EXCITATION = "excitation"
    INHIBITION = "inhibition"
    SUPPRESSION = "suppression"
    EDGE_WEIGHT_MODIFICATION = "edge_weight_modification"


class NeuralPerturbation(BaseModel):
    """
    Explicit specification of a neural perturbation applied to a set of target neurons.

    Magnitude is a dimensionless model parameter in [0.0, 1.0].
    It does NOT imply a percentage inhibition biologically.
    """
    target_neuron_ids: List[str] = Field(..., min_length=1, description="List of neuron IDs to perturb")
    effect: PerturbationEffect = Field(..., description="Type of perturbation effect")
    magnitude: float = Field(..., ge=0.0, le=1.0, description="Model magnitude parameter in [0, 1]")
    start_time: float = Field(0.0, ge=0.0, description="Simulation time when perturbation becomes active")
    duration: float = Field(..., gt=0.0, description="Duration in simulation seconds")
    mechanism: str = Field("computational_test", description="Model mechanism description")
    source: str = Field("user_defined", description="Source of perturbation (e.g. user_defined, literature)")
    evidence: Optional[str] = Field("unspecified", description="Evidence category (e.g. computational, experimental)")
    confidence: Optional[str] = Field("unspecified", description="Confidence level")

    @field_validator("target_neuron_ids")
    @classmethod
    def validate_targets_non_empty(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v if t and t.strip()]
        if not cleaned:
            raise ValueError("target_neuron_ids must contain at least one non-empty neuron ID")
        return cleaned


class SimulationConfig(BaseModel):
    """
    Configuration parameters for the discrete-time propagation engine.

    Conservative limits:
    - dt in [0.001, 1.0]
    - duration in [0.1, 50.0]
    - decay in [0.0, 1.0]
    - propagation_strength in [0.0, 5.0]
    - baseline_activity in [0.0, 1.0]
    """
    dt: float = Field(0.1, ge=0.001, le=1.0, description="Discrete timestep size in seconds")
    duration: float = Field(5.0, ge=0.1, le=50.0, description="Total simulation duration in seconds")
    decay: float = Field(0.85, ge=0.0, le=1.0, description="Activity decay/retention factor per step")
    propagation_strength: float = Field(0.5, ge=0.0, le=5.0, description="Coupling strength for input propagation")
    baseline_activity: float = Field(0.2, ge=0.0, le=1.0, description="Resting baseline activity level")
    min_activity: float = Field(0.0, ge=0.0, description="Lower activity bound")
    max_activity: float = Field(1.0, le=1.0, description="Upper activity bound")


class SimulationState(BaseModel):
    """Snapshot of network activity at a single simulation time point."""
    time: float
    neuron_activity: Dict[str, float]
    active_perturbations: List[NeuralPerturbation] = Field(default_factory=list)


class NetworkMetrics(BaseModel):
    """
    Network-level summary metrics for a simulation state.

    These are COMPUTATIONAL NETWORK METRICS, not behavioral metrics.
    """
    mean_activity: float
    active_neuron_count: int
    maximum_activity: float
    minimum_activity: float
    total_network_activity: float
    perturbed_neuron_activity: Dict[str, float]
    downstream_affected_neuron_count: int


class PropagationHopRecord(BaseModel):
    """
    Tracks computational propagation of perturbation effects through network hops.
    """
    neuron_id: str
    hop_distance: Optional[int] = None
    activity_change: float = 0.0
    time_of_change: Optional[float] = None


class SimulationProvenance(BaseModel):
    """Provenance metadata ensuring simulation reproducibility and source tracking."""
    simulation_id: str
    connectome_provider: str
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    is_synthetic: bool = True
    creation_timestamp: str
    model_version: str = "0.1.0-phase5"
    neuron_count: int
    connection_count: int
    config: SimulationConfig
    perturbations: List[NeuralPerturbation]


class NeuronDelta(BaseModel):
    """Comparison of individual neuron activity between baseline and perturbed simulations."""
    neuron_id: str
    cell_type: str
    region: str
    baseline_activity: float
    perturbed_activity: float
    delta_activity: float  # perturbed - baseline
    hop_distance: Optional[int] = None
    has_coordinates: bool = False
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class SimulationResult(BaseModel):
    """
    Complete output of a simulation run including baseline comparison and propagation tracking.
    """
    simulation_id: str
    config: SimulationConfig
    time_series: List[SimulationState]
    baseline_time_series: List[SimulationState]
    final_state: SimulationState
    baseline_final_state: SimulationState
    metrics: NetworkMetrics
    baseline_metrics: NetworkMetrics
    neuron_deltas: List[NeuronDelta]
    propagation_records: List[PropagationHopRecord]
    provenance: SimulationProvenance
    was_truncated: bool = False


class SimulationRunRequest(BaseModel):
    """Request payload to initiate a simulation run."""
    neuron_ids: Optional[List[str]] = None
    focal_neuron_id: Optional[str] = None
    hops: int = Field(1, ge=1, le=3)
    perturbations: List[NeuralPerturbation] = Field(default_factory=list)
    config: Optional[SimulationConfig] = None
