import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ConnectomeViewer } from './index';
import * as client from '../../api/client';

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
    runSimulation: vi.fn(),
    getSimulation: vi.fn(),
  };
});

const mockSyntheticMetadata: client.ConnectomeMetadata = {
  id: 'synthetic_connectome',
  description: 'Deterministic synthetic connectome',
  neuron_count: 3,
  connection_count: 2,
  provider_type: 'synthetic',
  is_synthetic: true,
};

const mockNeurons: client.Neuron[] = [
  {
    neuron_id: 'syn_neuron_0',
    cell_type: 'Sensory',
    region: 'Antennal Lobe',
    x: 0,
    y: 0,
    z: 0,
    has_coordinates: true,
  },
  {
    neuron_id: 'syn_neuron_1',
    cell_type: 'Interneuron',
    region: 'Lateral Horn',
    x: 10,
    y: 10,
    z: 10,
    has_coordinates: true,
  },
  {
    neuron_id: 'syn_neuron_2',
    cell_type: 'Motor',
    region: 'VNC',
    x: 20,
    y: 20,
    z: 20,
    has_coordinates: true,
  },
];

const mockSimResult: client.SimulationResult = {
  simulation_id: 'sim_test123',
  config: {
    dt: 0.1,
    duration: 3.0,
    decay: 0.85,
    propagation_strength: 0.5,
    baseline_activity: 0.2,
  },
  time_series: [
    { time: 0.0, neuron_activity: { syn_neuron_0: 0.7, syn_neuron_1: 0.2, syn_neuron_2: 0.2 } },
    { time: 1.0, neuron_activity: { syn_neuron_0: 0.7, syn_neuron_1: 0.45, syn_neuron_2: 0.2 } },
  ],
  baseline_time_series: [
    { time: 0.0, neuron_activity: { syn_neuron_0: 0.2, syn_neuron_1: 0.2, syn_neuron_2: 0.2 } },
    { time: 1.0, neuron_activity: { syn_neuron_0: 0.2, syn_neuron_1: 0.2, syn_neuron_2: 0.2 } },
  ],
  final_state: {
    time: 1.0,
    neuron_activity: { syn_neuron_0: 0.7, syn_neuron_1: 0.45, syn_neuron_2: 0.2 },
  },
  baseline_final_state: {
    time: 1.0,
    neuron_activity: { syn_neuron_0: 0.2, syn_neuron_1: 0.2, syn_neuron_2: 0.2 },
  },
  metrics: {
    mean_activity: 0.45,
    active_neuron_count: 2,
    maximum_activity: 0.7,
    minimum_activity: 0.2,
    total_network_activity: 1.35,
    perturbed_neuron_activity: { syn_neuron_0: 0.7 },
    downstream_affected_neuron_count: 1,
  },
  baseline_metrics: {
    mean_activity: 0.2,
    active_neuron_count: 0,
    maximum_activity: 0.2,
    minimum_activity: 0.2,
    total_network_activity: 0.6,
    perturbed_neuron_activity: {},
    downstream_affected_neuron_count: 0,
  },
  neuron_deltas: [
    {
      neuron_id: 'syn_neuron_0',
      cell_type: 'Sensory',
      region: 'Antennal Lobe',
      baseline_activity: 0.2,
      perturbed_activity: 0.7,
      delta_activity: 0.5,
      hop_distance: 0,
      has_coordinates: true,
      x: 0,
      y: 0,
      z: 0,
    },
    {
      neuron_id: 'syn_neuron_1',
      cell_type: 'Interneuron',
      region: 'Lateral Horn',
      baseline_activity: 0.2,
      perturbed_activity: 0.45,
      delta_activity: 0.25,
      hop_distance: 1,
      has_coordinates: true,
      x: 10,
      y: 10,
      z: 10,
    },
    {
      neuron_id: 'syn_neuron_2',
      cell_type: 'Motor',
      region: 'VNC',
      baseline_activity: 0.2,
      perturbed_activity: 0.2,
      delta_activity: 0.0,
      hop_distance: 2,
      has_coordinates: true,
      x: 20,
      y: 20,
      z: 20,
    },
  ],
  propagation_records: [
    { neuron_id: 'syn_neuron_0', hop_distance: 0, activity_change: 0.5, time_of_change: 0.0 },
    { neuron_id: 'syn_neuron_1', hop_distance: 1, activity_change: 0.25, time_of_change: 0.1 },
  ],
  provenance: {
    simulation_id: 'sim_test123',
    connectome_provider: 'synthetic',
    dataset_name: 'synthetic',
    is_synthetic: true,
    creation_timestamp: '2026-09-25T18:00:00Z',
    model_version: '0.1.0-phase5',
    neuron_count: 3,
    connection_count: 2,
    config: { dt: 0.1, duration: 3.0, baseline_activity: 0.2 },
    perturbations: [
      {
        target_neuron_ids: ['syn_neuron_0'],
        effect: 'activation',
        magnitude: 0.5,
        duration: 3.0,
      },
    ],
  },
  was_truncated: false,
};

describe('Phase 5 Simulation Frontend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (client.getConnectomeInfo as any).mockResolvedValue(mockSyntheticMetadata);
    (client.getNeurons as any).mockResolvedValue(mockNeurons);
    (client.runSimulation as any).mockResolvedValue(mockSimResult);
  });

  it('1. Simulation tab button switches to Simulation Panel with explicit disclaimer banner', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /inspector/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument();
    });

    const simTab = screen.getByRole('button', { name: /simulation/i });
    fireEvent.click(simTab);

    // Check computational simulation banner
    expect(screen.getByText('Computational Simulation')).toBeInTheDocument();
    expect(screen.getByText(/Normalized model activity ∈ \[0, 1\]/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Target Neuron ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Perturbation Effect')).toBeInTheDocument();
  });

  it('2. Target neuron selection works via text input', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));

    const input = screen.getByLabelText('Target Neuron ID') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'custom_neuron_99' } });
    expect(input.value).toBe('custom_neuron_99');
  });

  it('3. Perturbation effect selection works', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));

    const select = screen.getByLabelText('Perturbation Effect') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'inhibition' } });
    expect(select.value).toBe('inhibition');
  });

  it('4. Simulation starts and executes via Run Simulation button', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));

    const runBtn = screen.getByText('Run Simulation');
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(client.runSimulation).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Network-Level Metrics')).toBeInTheDocument();
      expect(screen.getByText('Mean Activity')).toBeInTheDocument();
    });
  });

  it('5. Simulation reset clears results and returns to initial state', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));

    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('Reset')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Reset'));

    expect(screen.queryByText('Network-Level Metrics')).not.toBeInTheDocument();
    expect(screen.queryByText('Reset')).not.toBeInTheDocument();
  });

  it('6. Visualization mode tabs (Perturbed, Baseline, Δ Activity) update mode', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));
    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('Perturbed')).toBeInTheDocument();
      expect(screen.getByText('Baseline')).toBeInTheDocument();
      expect(screen.getByText('Δ Activity')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Baseline'));
    fireEvent.click(screen.getByText('Δ Activity'));
    // Successfully switched modes without error
  });

  it('7. Displays baseline vs perturbed delta comparison and network metrics', async () => {
    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));
    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('0.450')).toBeInTheDocument(); // mean activity
      expect(screen.getByText('+0.500')).toBeInTheDocument(); // syn_neuron_0 delta
      expect(screen.getByText('+0.250')).toBeInTheDocument(); // syn_neuron_1 delta
    });
  });

  it('8. Error state is displayed when simulation API fails', async () => {
    (client.runSimulation as any).mockRejectedValue(new Error('Bounded subgraph extraction required'));

    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));
    fireEvent.click(screen.getByText('Run Simulation'));

    await waitFor(() => {
      expect(screen.getByText('Bounded subgraph extraction required')).toBeInTheDocument();
    });
  });

  it('9. Loading state appears during simulation run', async () => {
    let resolveSim: any;
    (client.runSimulation as any).mockReturnValue(
      new Promise((res) => {
        resolveSim = res;
      })
    );

    render(<ConnectomeViewer />);

    await waitFor(() => expect(screen.getByRole('button', { name: /simulation/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /simulation/i }));

    const runBtn = screen.getByText('Run Simulation');
    fireEvent.click(runBtn);

    expect(screen.getByText('Simulating...')).toBeInTheDocument();

    resolveSim(mockSimResult);
    await waitFor(() => {
      expect(screen.queryByText('Simulating...')).not.toBeInTheDocument();
    });
  });
});
