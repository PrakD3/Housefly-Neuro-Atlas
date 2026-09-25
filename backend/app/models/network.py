"""
Network Analysis Data Models for Drosophila-NeuroAtlas Phase 6.

Distinguishes:
- STRUCTURAL METRICS: Quantitative properties of the connectome graph itself.
- SIMULATION-DERIVED METRICS: Computational states and activity differences
  resulting from Phase 5 discrete-time neural perturbation simulations.

SCIENTIFIC PRINCIPLE:
Network metrics describe the analyzed computational graph and should not automatically
be interpreted as measurements of biological importance, causal influence,
or physiological toxicity.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class GraphStructuralMetrics(BaseModel):
    """
    Structural metrics calculated directly from the connectome graph.
    All metrics reflect directed graph topology unless explicitly noted.
    """
    neuron_count: int = Field(..., ge=0, description="Total number of neurons in the analyzed subgraph")
    connection_count: int = Field(..., ge=0, description="Total number of directed connections in the subgraph")
    density: float = Field(..., ge=0.0, le=1.0, description="Graph density: E / (V * (V - 1)) for directed graph")
    mean_in_degree: float = Field(..., ge=0.0, description="Average in-degree across all neurons")
    mean_out_degree: float = Field(..., ge=0.0, description="Average out-degree across all neurons")
    max_in_degree: int = Field(..., ge=0, description="Maximum in-degree among all neurons")
    max_out_degree: int = Field(..., ge=0, description="Maximum out-degree among all neurons")
    strongly_connected_components: int = Field(..., ge=0, description="Number of strongly connected components")
    weakly_connected_components: int = Field(..., ge=0, description="Number of weakly connected components")
    largest_wcc_size: int = Field(..., ge=0, description="Number of nodes in the largest weakly connected component")
    average_shortest_path_length: Optional[float] = Field(
        None,
        description="Average shortest path length on connected components where mathematically defined",
    )
    is_directed: bool = Field(True, description="Flag indicating directed graph definitions are used")
    is_dag: bool = Field(False, description="Whether the analyzed subgraph is a directed acyclic graph")


class CentralityMetricValue(BaseModel):
    """
    Modeled network centrality measures for an individual neuron.
    Terminology note: Centrality reflects graph structural position, NOT biological importance.
    """
    neuron_id: str = Field(..., description="Unique identifier of the neuron")
    in_degree_centrality: float = Field(..., ge=0.0, description="Fraction of incoming nodes connected to this node")
    out_degree_centrality: float = Field(..., ge=0.0, description="Fraction of outgoing nodes connected from this node")
    betweenness_centrality: float = Field(..., ge=0.0, description="Directed betweenness centrality fraction")
    closeness_centrality: float = Field(..., ge=0.0, description="Directed closeness centrality")


class TargetAnalysis(BaseModel):
    """
    Target-centered reachability and topological analysis for a perturbation target.
    """
    target_neuron_id: str = Field(..., description="Neuron ID of the perturbation target")
    in_degree: int = Field(..., ge=0, description="Number of incoming connections")
    out_degree: int = Field(..., ge=0, description="Number of outgoing connections")
    total_degree: int = Field(..., ge=0, description="Sum of in-degree and out-degree")
    upstream_neuron_count: int = Field(..., ge=0, description="Number of direct upstream pre-synaptic partners")
    downstream_neuron_count: int = Field(..., ge=0, description="Number of direct downstream post-synaptic partners")
    upstream_neurons: List[str] = Field(default_factory=list, description="IDs of direct upstream neighbors")
    downstream_neurons: List[str] = Field(default_factory=list, description="IDs of direct downstream partners")
    reachability_by_hop: Dict[int, List[str]] = Field(
        default_factory=dict,
        description="Downstream neuron IDs reached at each exact hop distance: {1: [...], 2: [...], ...}",
    )
    reachability_counts: Dict[int, int] = Field(
        default_factory=dict,
        description="Count of downstream neurons reached at each exact hop distance: {1: count, 2: count, ...}",
    )
    shortest_path_lengths_downstream: Dict[str, int] = Field(
        default_factory=dict,
        description="Directed shortest path length from target to reachable neurons",
    )


class ModelAffectedNeuron(BaseModel):
    """
    Per-neuron dynamic comparison between baseline and perturbed simulation states.
    Categorized as 'model-affected' if |delta_activity| exceeds the computational threshold.
    """
    neuron_id: str
    cell_type: str = "Unknown"
    region: str = "Unknown"
    baseline_activity: float
    perturbed_activity: float
    delta_activity: float  # perturbed - baseline
    absolute_delta: float  # abs(delta_activity)
    hop_distance: Optional[int] = None
    is_target: bool = False
    exceeds_threshold: bool = False
    has_coordinates: bool = False
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class TemporalNeuronMetrics(BaseModel):
    """
    Temporal summary metrics for an individual neuron across the simulation time series.
    All activity references are 'modeled activity' within the discrete-time graph simulation.
    """
    neuron_id: str
    initial_activity: float
    final_activity: float
    max_activity: float
    min_activity: float
    peak_absolute_change: float
    time_of_peak_change: float
    area_under_curve: float = Field(..., description="Trapezoidal integration of modeled activity over time")
    time_to_threshold: Optional[float] = Field(
        None,
        description="Simulation time when |delta(t)| first reached the threshold, or None if never reached",
    )


class PerturbationSummaryMetrics(BaseModel):
    """
    Network-level summary of computational perturbation propagation.
    """
    threshold: float = Field(..., description="Computational delta threshold used to classify affected neurons")
    total_baseline_activity: float
    total_perturbed_activity: float
    delta_total_activity: float
    mean_baseline_activity: float
    mean_perturbed_activity: float
    mean_absolute_activity_change: float
    max_absolute_activity_change: float
    model_affected_neuron_count: int
    model_affected_neuron_fraction: float
    target_activity_summary: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Per-target activity shift: {target_id: {'baseline': x, 'perturbed': y, 'delta': z}}",
    )


class PerturbationAnalysis(BaseModel):
    """
    Complete perturbation and propagation analysis bundle.
    """
    target_neuron_ids: List[str]
    threshold: float
    affected_neurons: List[ModelAffectedNeuron]
    network_summary: PerturbationSummaryMetrics
    temporal_summary: Optional[List[TemporalNeuronMetrics]] = None


class NetworkAnalysisProvenance(BaseModel):
    """
    Provenance tracking for network analysis results, preserving dataset and simulation origin.
    """
    simulation_id: str
    connectome_provider: str
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    is_synthetic: bool = True
    analysis_timestamp: str
    analysis_version: str = "0.1.0-phase6"
    threshold: float
    max_hops: int
    neuron_count: int
    connection_count: int


class NetworkAnalysisResult(BaseModel):
    """
    Complete typed result of the Network Analysis Engine.
    """
    simulation_id: str
    network_metrics: GraphStructuralMetrics
    centrality: List[CentralityMetricValue]
    target_analysis: List[TargetAnalysis]
    perturbation_analysis: PerturbationAnalysis
    provenance: NetworkAnalysisProvenance


class NetworkAnalysisRequest(BaseModel):
    """
    Request payload to run network analysis on a prior simulation run.
    """
    simulation_id: str = Field(..., min_length=1, description="ID of the completed simulation")
    threshold: float = Field(0.05, ge=0.0, le=1.0, description="Computational delta activity threshold")
    max_hops: int = Field(3, ge=1, le=10, description="Maximum reachability hop depth to calculate")
    metrics: Optional[List[str]] = Field(
        None,
        description="Optional subset of metrics to calculate (default: all supported metrics)",
    )

    @field_validator("simulation_id")
    @classmethod
    def validate_simulation_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("simulation_id cannot be empty")
        return s
