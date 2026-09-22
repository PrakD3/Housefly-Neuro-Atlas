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
  x: number;
  y: number;
  z: number;
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
}

export interface SubgraphResponse {
  neurons: Neuron[];
  connections: Connection[];
}

/**
 * Check backend health status.
 * @returns The health response from the backend.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Get connectome metadata.
 */
export async function getConnectomeInfo(): Promise<ConnectomeMetadata> {
  const response = await fetch(`${API_BASE_URL}/connectome/info`);
  if (!response.ok) {
    throw new Error(`Failed to fetch connectome info: ${response.status}`);
  }
  return response.json();
}

/**
 * Get all neurons (or filtered).
 */
export async function getNeurons(cellType?: string, region?: string): Promise<Neuron[]> {
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
 * Get neighborhood for a neuron.
 */
export async function getNeuronNeighbors(neuronId: string, hops: number = 1): Promise<SubgraphResponse> {
  const response = await fetch(`${API_BASE_URL}/connectome/neurons/${neuronId}/neighbors?hops=${hops}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch neighbors: ${response.status}`);
  }
  return response.json();
}
