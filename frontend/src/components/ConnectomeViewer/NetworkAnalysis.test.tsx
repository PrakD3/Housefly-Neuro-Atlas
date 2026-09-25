import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NetworkAnalysisPanel } from './NetworkAnalysisPanel';
import * as client from '../../api/client';
import {
  Neuron,
  NetworkAnalysisResult,
  SimulationResult,
} from '../../api/client';

// Mock client methods
vi.mock('../../api/client', async () => {
  const actual = await vi.importActual('../../api/client');
  return {
    ...actual,
    runNetworkAnalysis: vi.fn(),
  };
});

describe('Phase 6 Network Analysis Frontend Integration', () => {
  const mockNeurons: Neuron[] = [
    { neuron_id: 'N1', cell_type: 'Sensory', region: 'Protocerebrum', x: 0, y: 0, z: 0, has_coordinates: true },
    { neuron_id: 'N2', cell_type: 'Interneuron', region: 'Protocerebrum', x: 5, y: 5, z: 5, has_coordinates: true },
    { neuron_id: 'N3', cell_type: 'Motor', region: 'VNC', x: 10, y: 10, z: 10, has_coordinates: true },
  ];

  const mockSimulationResult: SimulationResult = {
    simulation_id: 'sim_123',
    config: { dt: 0.1, duration: 2.0, decay: 0.85, baseline_activity: 0.2 },
    time_series: [
      { time: 0.0, neuron_activity: { N1: 0.2, N2: 0.2, N3: 0.2 } },
      { time: 2.0, neuron_activity: { N1: 0.8, N2: 0.5, N3: 0.25 } },
    ],
    baseline_time_series: [
      { time: 0.0, neuron_activity: { N1: 0.2, N2: 0.2, N3: 0.2 } },
      { time: 2.0, neuron_activity: { N1: 0.2, N2: 0.2, N3: 0.2 } },
    ],
    final_state: { time: 2.0, neuron_activity: { N1: 0.8, N2: 0.5, N3: 0.25 } },
    baseline_final_state: { time: 2.0, neuron_activity: { N1: 0.2, N2: 0.2, N3: 0.2 } },
    metrics: {
      mean_activity: 0.516,
      active_neuron_count: 3,
      maximum_activity: 0.8,
      minimum_activity: 0.25,
      total_network_activity: 1.55,
      perturbed_neuron_activity: { N1: 0.8 },
      downstream_affected_neuron_count: 2,
    },
    baseline_metrics: {
      mean_activity: 0.2,
      active_neuron_count: 3,
      maximum_activity: 0.2,
      minimum_activity: 0.2,
      total_network_activity: 0.6,
      perturbed_neuron_activity: { N1: 0.2 },
      downstream_affected_neuron_count: 0,
    },
    neuron_deltas: [
      {
        neuron_id: 'N1',
        cell_type: 'Sensory',
        region: 'Protocerebrum',
        baseline_activity: 0.2,
        perturbed_activity: 0.8,
        delta_activity: 0.6,
        hop_distance: 0,
        has_coordinates: true,
        x: 0, y: 0, z: 0,
      },
      {
        neuron_id: 'N2',
        cell_type: 'Interneuron',
        region: 'Protocerebrum',
        baseline_activity: 0.2,
        perturbed_activity: 0.5,
        delta_activity: 0.3,
        hop_distance: 1,
        has_coordinates: true,
        x: 5, y: 5, z: 5,
      },
      {
        neuron_id: 'N3',
        cell_type: 'Motor',
        region: 'VNC',
        baseline_activity: 0.2,
        perturbed_activity: 0.25,
        delta_activity: 0.05,
        hop_distance: 2,
        has_coordinates: true,
        x: 10, y: 10, z: 10,
      },
    ],
    propagation_records: [],
    provenance: {
      simulation_id: 'sim_123',
      connectome_provider: 'synthetic_test',
      is_synthetic: true,
      creation_timestamp: '2026-09-25T12:00:00Z',
      model_version: '0.1.0-phase5',
      neuron_count: 3,
      connection_count: 2,
      config: { dt: 0.1, duration: 2.0 },
      perturbations: [{
        target_neuron_ids: ['N1'],
        effect: 'activation',
        magnitude: 0.6,
        duration: 2.0,
      }],
    },
    was_truncated: false,
  };

  const mockAnalysisResult: NetworkAnalysisResult = {
    simulation_id: 'sim_123',
    network_metrics: {
      neuron_count: 3,
      connection_count: 2,
      density: 0.333333,
      mean_in_degree: 0.6667,
      mean_out_degree: 0.6667,
      max_in_degree: 1,
      max_out_degree: 1,
      strongly_connected_components: 3,
      weakly_connected_components: 1,
      largest_wcc_size: 3,
      average_shortest_path_length: 1.3333,
      is_directed: true,
      is_dag: true,
    },
    centrality: [
      { neuron_id: 'N2', betweenness_centrality: 1.0, in_degree_centrality: 0.5, out_degree_centrality: 0.5, closeness_centrality: 0.5 },
      { neuron_id: 'N1', betweenness_centrality: 0.0, in_degree_centrality: 0.0, out_degree_centrality: 0.5, closeness_centrality: 0.5 },
      { neuron_id: 'N3', betweenness_centrality: 0.0, in_degree_centrality: 0.5, out_degree_centrality: 0.0, closeness_centrality: 0.0 },
    ],
    target_analysis: [
      {
        target_neuron_id: 'N1',
        in_degree: 0,
        out_degree: 1,
        total_degree: 1,
        upstream_neuron_count: 0,
        downstream_neuron_count: 1,
        upstream_neurons: [],
        downstream_neurons: ['N2'],
        reachability_by_hop: { 1: ['N2'], 2: ['N3'], 3: [] },
        reachability_counts: { 1: 1, 2: 1, 3: 0 },
        shortest_path_lengths_downstream: { N2: 1, N3: 2 },
      },
    ],
    perturbation_analysis: {
      target_neuron_ids: ['N1'],
      threshold: 0.05,
      affected_neurons: [
        {
          neuron_id: 'N1',
          cell_type: 'Sensory',
          region: 'Protocerebrum',
          baseline_activity: 0.2,
          perturbed_activity: 0.8,
          delta_activity: 0.6,
          absolute_delta: 0.6,
          hop_distance: 0,
          is_target: true,
          exceeds_threshold: true,
          has_coordinates: true,
          x: 0, y: 0, z: 0,
        },
        {
          neuron_id: 'N2',
          cell_type: 'Interneuron',
          region: 'Protocerebrum',
          baseline_activity: 0.2,
          perturbed_activity: 0.5,
          delta_activity: 0.3,
          absolute_delta: 0.3,
          hop_distance: 1,
          is_target: false,
          exceeds_threshold: true,
          has_coordinates: true,
          x: 5, y: 5, z: 5,
        },
        {
          neuron_id: 'N3',
          cell_type: 'Motor',
          region: 'VNC',
          baseline_activity: 0.2,
          perturbed_activity: 0.25,
          delta_activity: 0.05,
          absolute_delta: 0.05,
          hop_distance: 2,
          is_target: false,
          exceeds_threshold: true,
          has_coordinates: true,
          x: 10, y: 10, z: 10,
        },
      ],
      network_summary: {
        threshold: 0.05,
        total_baseline_activity: 0.6,
        total_perturbed_activity: 1.55,
        delta_total_activity: 0.95,
        mean_baseline_activity: 0.2,
        mean_perturbed_activity: 0.5167,
        mean_absolute_activity_change: 0.3167,
        max_absolute_activity_change: 0.6,
        model_affected_neuron_count: 3,
        model_affected_neuron_fraction: 1.0,
        target_activity_summary: {
          N1: { baseline: 0.2, perturbed: 0.8, delta: 0.6 },
        },
      },
      temporal_summary: [],
    },
    provenance: {
      simulation_id: 'sim_123',
      connectome_provider: 'synthetic_test',
      is_synthetic: true,
      analysis_timestamp: '2026-09-25T12:05:00Z',
      analysis_version: '0.1.0-phase6',
      threshold: 0.05,
      max_hops: 3,
      neuron_count: 3,
      connection_count: 2,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders empty state prompt when no simulation has been run', () => {
    const handleGoToSim = vi.fn();
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={null}
        onSelectNeuron={vi.fn()}
        analysisResult={null}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={handleGoToSim}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    expect(screen.getByText('Network Analysis Engine')).toBeInTheDocument();
    expect(screen.getByText('Go to Simulation Tab')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Go to Simulation Tab'));
    expect(handleGoToSim).toHaveBeenCalled();
  });

  it('2. Renders controls when simulation result is available', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={null}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    expect(screen.getByText('Network Analysis')).toBeInTheDocument();
    expect(screen.getByText('Scientific Principle:')).toBeInTheDocument();
    expect(screen.getByText('Run Network Analysis')).toBeInTheDocument();
  });

  it('3. Triggers runNetworkAnalysis on button click', async () => {
    const handleAnalysisResult = vi.fn();
    vi.mocked(client.runNetworkAnalysis).mockResolvedValue(mockAnalysisResult);

    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={null}
        onAnalysisResult={handleAnalysisResult}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Run Network Analysis'));

    await waitFor(() => {
      expect(client.runNetworkAnalysis).toHaveBeenCalledWith({
        simulation_id: 'sim_123',
        threshold: 0.05,
        max_hops: 3,
      });
      expect(handleAnalysisResult).toHaveBeenCalledWith(mockAnalysisResult);
    });
  });

  it('4. Renders summary and perturbation metrics when analysisResult is present', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    expect(screen.getByText('Model-Affected Neurons')).toBeInTheDocument();
    expect(screen.getByText('0.6000')).toBeInTheDocument(); // Max shift
    expect(screen.getByText('+0.9500')).toBeInTheDocument(); // Delta total
  });

  it('5. Switches to affected neurons list and renders rows', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Affected'));
    expect(screen.getByText('N1')).toBeInTheDocument();
    expect(screen.getByText('+0.600')).toBeInTheDocument();
    expect(screen.getByText('N2')).toBeInTheDocument();
    expect(screen.getByText('+0.300')).toBeInTheDocument();
  });

  it('6. Switches to structural graph topology section', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Structure'));
    expect(screen.getByText('Connectome Subgraph Topology')).toBeInTheDocument();
    expect(screen.getByText('Directed Connections:')).toBeInTheDocument();
    expect(screen.getByText('Weakly Connected Components:')).toBeInTheDocument();
  });

  it('7. Switches to target reachability analysis', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Targets'));
    expect(screen.getByText('★ Target: N1')).toBeInTheDocument();
    expect(screen.getByText('1 partners')).toBeInTheDocument();
    expect(screen.getByText('Hop 1')).toBeInTheDocument();
    expect(screen.getByText('Hop 2')).toBeInTheDocument();
  });

  it('8. Switches to modeled centrality ranking section', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Centrality'));
    expect(screen.getByText('Highest modeled network centrality in the analyzed subgraph:')).toBeInTheDocument();
    expect(screen.getByText('1.0000')).toBeInTheDocument(); // N2 betweenness
  });

  it('9. Switches to analytical charts section and renders bars', () => {
    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={vi.fn()}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Charts'));
    expect(screen.getByText('Activity Change Distribution (|Δ|)')).toBeInTheDocument();
    expect(screen.getByText('Network Modeled Activity Shift')).toBeInTheDocument();
  });

  it('10. Displays error message when API call fails and toggle highlight affected works', async () => {
    const handleToggle = vi.fn();
    vi.mocked(client.runNetworkAnalysis).mockRejectedValue(new Error('Backend error: graph bounds exceeded'));

    render(
      <NetworkAnalysisPanel
        neurons={mockNeurons}
        selectedNeuron={null}
        simulationResult={mockSimulationResult}
        onSelectNeuron={vi.fn()}
        analysisResult={mockAnalysisResult}
        onAnalysisResult={vi.fn()}
        onGoToSimulation={vi.fn()}
        highlightAffectedOnly={false}
        onToggleHighlightAffected={handleToggle}
        activeHopFilter="all"
        onSelectHopFilter={vi.fn()}
      />
    );

    // Test toggle button
    fireEvent.click(screen.getByText('Highlight Affected'));
    expect(handleToggle).toHaveBeenCalled();

    // Test error state
    fireEvent.click(screen.getByText('Update Network Analysis'));
    await waitFor(() => {
      expect(screen.getByText('Backend error: graph bounds exceeded')).toBeInTheDocument();
    });
  });
});
