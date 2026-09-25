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

