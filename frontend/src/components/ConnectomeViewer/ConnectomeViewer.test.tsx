import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ConnectomeViewer } from './index';
import * as client from '../../api/client';
import { computeTransform, applyTransform, toScenePosition } from './VisualizationTransform';

// Mock Three.js / R3F Canvas and hooks
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="r3f-canvas">{children}</div>,
  useFrame: vi.fn(),
}));

vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  QuadraticBezierLine: () => null,
}));

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual('../../api/client');
  return {
    ...actual,
    getConnectomeInfo: vi.fn(),
    getNeurons: vi.fn(),
    getNeuronNeighbors: vi.fn(),
    getNeighborhood: vi.fn(),
    searchNeurons: vi.fn(),
  };
});

describe('VisualizationTransform', () => {
  it('returns null for neurons without coordinates or has_coordinates=false', () => {
    const neuronNoCoords: client.Neuron = {
      neuron_id: '1001',
      cell_type: 'DNge104',
      region: 'GNG',
      x: null,
      y: null,
      z: null,
      has_coordinates: false,
    };
    const transform = computeTransform([neuronNoCoords]);
    const pos = toScenePosition(neuronNoCoords, transform);
    expect(pos).toBeNull();
  });

  it('normalizes voxel coordinates to scene target diameter', () => {
    const n1: client.Neuron = {
      neuron_id: '1',
      cell_type: 'typeA',
      region: 'GNG',
      x: 100000,
      y: 200000,
      z: 50000,
      has_coordinates: true,
    };
    const n2: client.Neuron = {
      neuron_id: '2',
      cell_type: 'typeB',
      region: 'GNG',
      x: 150000,
      y: 200000,
      z: 50000,
      has_coordinates: true,
    };

    const transform = computeTransform([n1, n2], 50);
    // Span in X is 50000, scale is 50 / 50000 = 0.001
    expect(transform.scale).toBeCloseTo(0.001);
    expect(transform.center).toEqual([125000, 200000, 50000]);

    const pos1 = toScenePosition(n1, transform);
    const pos2 = toScenePosition(n2, transform);
    expect(pos1).toEqual([-25, 0, 0]);
    expect(pos2).toEqual([25, 0, 0]);

    const transformed = applyTransform([100000, 200000, 50000], transform);
    expect(transformed).toEqual([-25, 0, 0]);
  });
});

describe('ConnectomeViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Synthetic mode still renders', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'synthetic_v1',
      description: 'Synthetic connectome',
      neuron_count: 50,
      connection_count: 100,
      provider_type: 'SyntheticConnectomeProvider',
      is_synthetic: true,
    });
    vi.mocked(client.getNeurons).mockResolvedValue([
      {
        neuron_id: 'syn_neuron_0',
        cell_type: 'Sensory',
        region: 'Region_A',
        x: 10,
        y: 20,
        z: 30,
        has_coordinates: true,
      },
    ]);

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByText('SYNTHETIC DATA')).toBeInTheDocument();
      expect(screen.getByText('Cell Type')).toBeInTheDocument();
    });
  });

  it('2. Real mode shows neuron loader input', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real Drosophila connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
      expect(screen.getByText('Real Connectome Query')).toBeInTheDocument();
    });
  });

  it('3. Real metadata badge shows dataset name', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real Drosophila connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByText('REAL CONNECTOME')).toBeInTheDocument();
      expect(screen.getByText('male-cns v1.0')).toBeInTheDocument();
    });
  });

  it('4. Neuron lookup triggers neighborhood fetch', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    vi.mocked(client.getNeighborhood).mockResolvedValue({
      neurons: [
        {
          neuron_id: '720575940614131',
          cell_type: 'DNge104',
          region: 'GNG',
          x: 100000,
          y: 200000,
          z: 300000,
          has_coordinates: true,
        },
      ],
      connections: [],
      neuron_count: 1,
      connection_count: 0,
      was_truncated: false,
      max_neurons_limit: 500,
      max_connections_limit: 2000,
      query_neuron_id: '720575940614131',
      hops: 1,
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Neuron Body ID');
    fireEvent.change(input, { target: { value: '720575940614131' } });

    const submitBtn = screen.getByText('Load Subgraph');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(client.getNeighborhood).toHaveBeenCalledWith('720575940614131', 1);
      expect(screen.getByText('Current Focal Neuron:')).toBeInTheDocument();
    });
  });

  it('5. Loading state appears during fetch', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    let resolvePromise: any;
    const slowPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    vi.mocked(client.getNeighborhood).mockReturnValue(slowPromise as any);

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Neuron Body ID');
    fireEvent.change(input, { target: { value: '720575940614131' } });

    const submitBtn = screen.getByText('Load Subgraph');
    fireEvent.click(submitBtn);

    expect(screen.getByText('Loading Subgraph...')).toBeInTheDocument();

    resolvePromise({
      neurons: [],
      connections: [],
      neuron_count: 0,
      connection_count: 0,
      was_truncated: false,
      max_neurons_limit: 500,
      max_connections_limit: 2000,
      query_neuron_id: '720575940614131',
      hops: 1,
    });
  });

  it('6. 503 error shows "Real connectome unavailable"', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    const error = new Error('Real connectome unavailable — authentication required') as any;
    error.status = 503;
    vi.mocked(client.getNeighborhood).mockRejectedValue(error);

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Neuron Body ID');
    fireEvent.change(input, { target: { value: '12345' } });
    fireEvent.click(screen.getByText('Load Subgraph'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('REAL CONNECTOME UNAVAILABLE')).toBeInTheDocument();
    });
  });

  it('7. 404 shows "Neuron not found"', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    const error = new Error("Neuron '999999' not found") as any;
    error.status = 404;
    vi.mocked(client.getNeighborhood).mockRejectedValue(error);

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Neuron Body ID');
    fireEvent.change(input, { target: { value: '999999' } });
    fireEvent.click(screen.getByText('Load Subgraph'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('NEURON NOT FOUND')).toBeInTheDocument();
    });
  });

  it('8. null coordinates: neuron has no coordinates and inspector shows "No spatial data"', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    vi.mocked(client.getNeighborhood).mockResolvedValue({
      neurons: [
        {
          neuron_id: '720575940614131',
          cell_type: 'DNge104',
          region: 'GNG',
          x: null,
          y: null,
          z: null,
          has_coordinates: false,
        },
      ],
      connections: [],
      neuron_count: 1,
      connection_count: 0,
      was_truncated: false,
      max_neurons_limit: 500,
      max_connections_limit: 2000,
      query_neuron_id: '720575940614131',
      hops: 1,
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByLabelText('Neuron Body ID')).toBeInTheDocument();
    });

    const input = screen.getByLabelText('Neuron Body ID');
    fireEvent.change(input, { target: { value: '720575940614131' } });
    fireEvent.click(screen.getByText('Load Subgraph'));

    await waitFor(() => {
      expect(screen.getByText('No spatial data')).toBeInTheDocument();
    });
  });

  it('9. Provider badge changes correctly based on metadata', async () => {
    // Verify real mode shows REAL CONNECTOME badge and NOT SYNTHETIC DATA
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'male-cns',
      dataset_version: 'v1.0',
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByText('REAL CONNECTOME')).toBeInTheDocument();
      expect(screen.queryByText('SYNTHETIC DATA')).not.toBeInTheDocument();
      // Footer dataset badge should show the version
      expect(screen.getByText('Real Connectome Data')).toBeInTheDocument();
    });
  });

  it('10. Dataset/version visible in left panel for real mode', async () => {
    vi.mocked(client.getConnectomeInfo).mockResolvedValue({
      id: 'male-cns:v1.0',
      description: 'Real Drosophila connectome',
      neuron_count: -1,
      connection_count: -1,
      provider_type: 'RealDrosophilaConnectomeProvider',
      is_synthetic: false,
      dataset_name: 'Drosophila Male CNS',
      dataset_version: 'v1.0',
    });

    render(<ConnectomeViewer />);

    await waitFor(() => {
      // Left panel Dataset row shows the dataset_name value
      expect(screen.getByText('Drosophila Male CNS')).toBeInTheDocument();
      // Left panel Version row shows the dataset_version value
      // (also in header badge — getAllByText handles multiple matches)
      expect(screen.getAllByText('v1.0').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Real Connectome Data')).toBeInTheDocument();
    });
  });
});
