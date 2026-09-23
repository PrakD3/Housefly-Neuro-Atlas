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
