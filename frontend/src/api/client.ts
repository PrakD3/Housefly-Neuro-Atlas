/**
 * API client for communicating with the Drosophila-NeuroAtlas backend.
 */

const API_BASE_URL = "http://localhost:8000";

export interface HealthResponse {
  status: string;
}

export interface Neuron {
  neuron_id: string;
  cell_type: string;
  region: string;
  /**
   * Spatial coordinates from the real connectome (somaLocation, 8 nm/voxel).
   * These are null when the source data has no somaLocation for this neuron.
   *
   * IMPORTANT: null means data is absent. NEVER treat null as (0, 0, 0).
   * Always check has_coordinates before using x/y/z.
   */
  x: number | null;
  y: number | null;
  z: number | null;
  /** True only when x, y, z are all non-null. Gate all 3D placement on this. */
  has_coordinates: boolean;
  neurotransmitter?: string | null;
  status?: string | null;
  instance?: string | null;
}

export interface Connection {
  source_neuron: string;
  target_neuron: string;
  weight: number;
}

export interface ConnectomeMetadata {
  id: string;
  description: string;
  neuron_count: number;
  connection_count: number;
  provider_type: string;
  is_synthetic: boolean;
  // Real-data provenance fields — present when is_synthetic=false
  dataset_name?: string | null;
  dataset_version?: string | null;
  organism?: string | null;
  sex?: string | null;
  source_url?: string | null;
  license?: string | null;
}

export interface SubgraphResponse {
  neurons: Neuron[];
  connections: Connection[];
}

export interface SubgraphProvenance {
  dataset_name?: string | null;
  dataset_version?: string | null;
  is_synthetic: boolean;
  query_timestamp?: string | null;
}

export interface BoundedSubgraphResponse extends SubgraphResponse {
  neuron_count: number;
  connection_count: number;
  was_truncated: boolean;
  max_neurons_limit: number;
  max_connections_limit: number;
  query_neuron_id: string;
  hops: number;
  provenance?: SubgraphProvenance | null;
}

/**
 * Check backend health status.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Get connectome metadata (identifies whether real or synthetic).
 */
export async function getConnectomeInfo(): Promise<ConnectomeMetadata> {
  const response = await fetch(`${API_BASE_URL}/connectome/info`);
  if (!response.ok) {
    throw new Error(`Failed to fetch connectome info: ${response.status}`);
  }
  return response.json();
}

/**
 * Get neurons optionally filtered by cell type and/or region.
 * For the real connectome at least one filter must be supplied.
 */
export async function getNeurons(
  cellType?: string,
  region?: string
): Promise<Neuron[]> {
  const params = new URLSearchParams();
  if (cellType) params.append("cell_type", cellType);
  if (region) params.append("region", region);

  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/connectome/neurons${query}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch neurons: ${response.status}`);
  }
  return response.json();
}

/**
 * Get a single neuron by ID.
 */
export async function getNeuron(neuronId: string): Promise<Neuron> {
  const response = await fetch(
    `${API_BASE_URL}/connectome/neurons/${neuronId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch neuron ${neuronId}: ${response.status}`);
  }
  return response.json();
}

/**
 * Get neighborhood subgraph for a neuron.
 */
export async function getNeuronNeighbors(
  neuronId: string,
  hops: number = 1
): Promise<SubgraphResponse> {
  const response = await fetch(
    `${API_BASE_URL}/connectome/neurons/${neuronId}/neighbors?hops=${hops}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch neighbors: ${response.status}`);
  }
  return response.json();
}

/**
 * Get bounded neighborhood subgraph for a neuron with server-enforced limits.
 */
export async function getNeighborhood(
  neuronId: string,
  hops: number = 1,
  maxNeurons?: number,
  maxConnections?: number
): Promise<BoundedSubgraphResponse> {
  const params = new URLSearchParams({
    neuron_id: neuronId,
    hops: hops.toString(),
  });
  if (maxNeurons) params.append("max_neurons", maxNeurons.toString());
  if (maxConnections) params.append("max_connections", maxConnections.toString());

  const response = await fetch(
    `${API_BASE_URL}/connectome/neighborhood?${params.toString()}`
  );
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Failed to fetch neighborhood: ${response.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.json();
}

/**
 * Search neurons by ID, cell type, instance, or region.
 */
export async function searchNeurons(
  query: string,
  limit: number = 20
): Promise<Neuron[]> {
  const params = new URLSearchParams({
    query,
    limit: limit.toString(),
  });
  const response = await fetch(
    `${API_BASE_URL}/connectome/search?${params.toString()}`
  );
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Failed to search neurons: ${response.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.json();
}

// =====================================================================
// Phase 5: Computational Neural Perturbation Simulation Types & APIs
// =====================================================================

export type PerturbationEffect =
  | "activation"
  | "excitation"
  | "inhibition"
  | "suppression"
  | "edge_weight_modification";

export interface NeuralPerturbation {
  target_neuron_ids: string[];
  effect: PerturbationEffect;
  magnitude: number;
  start_time?: number;
  duration: number;
  mechanism?: string;
  source?: string;
  evidence?: string;
  confidence?: string;
}

export interface SimulationConfig {
  dt?: number;
  duration?: number;
  decay?: number;
  propagation_strength?: number;
  baseline_activity?: number;
  min_activity?: number;
  max_activity?: number;
}

export interface SimulationState {
  time: number;
  neuron_activity: Record<string, number>;
  active_perturbations?: NeuralPerturbation[];
}

export interface NetworkMetrics {
  mean_activity: number;
  active_neuron_count: number;
  maximum_activity: number;
  minimum_activity: number;
  total_network_activity: number;
  perturbed_neuron_activity: Record<string, number>;
  downstream_affected_neuron_count: number;
}

export interface PropagationHopRecord {
  neuron_id: string;
  hop_distance?: number | null;
  activity_change: number;
  time_of_change?: number | null;
}

export interface SimulationProvenance {
  simulation_id: string;
  connectome_provider: string;
  dataset_name?: string | null;
  dataset_version?: string | null;
  is_synthetic: boolean;
  creation_timestamp: string;
  model_version: string;
  neuron_count: number;
  connection_count: number;
  config: SimulationConfig;
  perturbations: NeuralPerturbation[];
}

export interface NeuronDelta {
  neuron_id: string;
  cell_type: string;
  region: string;
  baseline_activity: number;
  perturbed_activity: number;
  delta_activity: number;
  hop_distance?: number | null;
  has_coordinates: boolean;
  x?: number | null;
  y?: number | null;
  z?: number | null;
}

export interface SimulationResult {
  simulation_id: string;
  config: SimulationConfig;
  time_series: SimulationState[];
  baseline_time_series: SimulationState[];
  final_state: SimulationState;
  baseline_final_state: SimulationState;
  metrics: NetworkMetrics;
  baseline_metrics: NetworkMetrics;
  neuron_deltas: NeuronDelta[];
  propagation_records: PropagationHopRecord[];
  provenance: SimulationProvenance;
  was_truncated: boolean;
}

export interface SimulationRunRequest {
  neuron_ids?: string[];
  focal_neuron_id?: string;
  hops?: number;
  perturbations: NeuralPerturbation[];
  config?: SimulationConfig;
}

/**
 * Execute a computational neural perturbation simulation on a bounded subgraph.
 */
export async function runSimulation(
  request: SimulationRunRequest
): Promise<SimulationResult> {
  const response = await fetch(`${API_BASE_URL}/simulations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Simulation failed: ${response.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.json();
}

/**
 * Retrieve the results of a previously executed simulation run.
 */
export async function getSimulation(
  simulationId: string
): Promise<SimulationResult> {
  const response = await fetch(`${API_BASE_URL}/simulations/${simulationId}`);
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Failed to fetch simulation: ${response.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.json();
}

// =====================================================================
// Phase 6: Network Analysis Types & APIs
// =====================================================================

export interface GraphStructuralMetrics {
  neuron_count: number;
  connection_count: number;
  density: number;
  mean_in_degree: number;
  mean_out_degree: number;
  max_in_degree: number;
  max_out_degree: number;
  strongly_connected_components: number;
  weakly_connected_components: number;
  largest_wcc_size: number;
  average_shortest_path_length?: number | null;
  is_directed: boolean;
  is_dag: boolean;
}

export interface CentralityMetricValue {
  neuron_id: string;
  in_degree_centrality: number;
  out_degree_centrality: number;
  betweenness_centrality: number;
  closeness_centrality: number;
}

export interface TargetAnalysis {
  target_neuron_id: string;
  in_degree: number;
  out_degree: number;
  total_degree: number;
  upstream_neuron_count: number;
  downstream_neuron_count: number;
  upstream_neurons: string[];
  downstream_neurons: string[];
  reachability_by_hop: Record<number, string[]>;
  reachability_counts: Record<number, number>;
  shortest_path_lengths_downstream: Record<string, number>;
}

export interface ModelAffectedNeuron {
  neuron_id: string;
  cell_type: string;
  region: string;
  baseline_activity: number;
  perturbed_activity: number;
  delta_activity: number;
  absolute_delta: number;
  hop_distance?: number | null;
  is_target: boolean;
  exceeds_threshold: boolean;
  has_coordinates: boolean;
  x?: number | null;
  y?: number | null;
  z?: number | null;
}

export interface TemporalNeuronMetrics {
  neuron_id: string;
  initial_activity: number;
  final_activity: number;
  max_activity: number;
  min_activity: number;
  peak_absolute_change: number;
  time_of_peak_change: number;
  area_under_curve: number;
  time_to_threshold?: number | null;
}

export interface PerturbationSummaryMetrics {
  threshold: number;
  total_baseline_activity: number;
  total_perturbed_activity: number;
  delta_total_activity: number;
  mean_baseline_activity: number;
  mean_perturbed_activity: number;
  mean_absolute_activity_change: number;
  max_absolute_activity_change: number;
  model_affected_neuron_count: number;
  model_affected_neuron_fraction: number;
  target_activity_summary: Record<string, Record<string, number>>;
}

export interface PerturbationAnalysis {
  target_neuron_ids: string[];
  threshold: number;
  affected_neurons: ModelAffectedNeuron[];
  network_summary: PerturbationSummaryMetrics;
  temporal_summary?: TemporalNeuronMetrics[] | null;
}

export interface NetworkAnalysisProvenance {
  simulation_id: string;
  connectome_provider: string;
  dataset_name?: string | null;
  dataset_version?: string | null;
  is_synthetic: boolean;
  analysis_timestamp: string;
  analysis_version: string;
  threshold: number;
  max_hops: number;
  neuron_count: number;
  connection_count: number;
}

export interface NetworkAnalysisResult {
  simulation_id: string;
  network_metrics: GraphStructuralMetrics;
  centrality: CentralityMetricValue[];
  target_analysis: TargetAnalysis[];
  perturbation_analysis: PerturbationAnalysis;
  provenance: NetworkAnalysisProvenance;
}

export interface NetworkAnalysisRequest {
  simulation_id: string;
  threshold?: number;
  max_hops?: number;
  metrics?: string[];
}

/**
 * Execute network analysis on a completed simulation.
 */
export async function runNetworkAnalysis(
  request: NetworkAnalysisRequest
): Promise<NetworkAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analysis/network`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || `Network analysis failed: ${response.status}`;
    const err = new Error(message) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.json();
}


