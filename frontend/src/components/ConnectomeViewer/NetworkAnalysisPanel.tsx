import React, { useState, useMemo } from 'react';
import {
  Neuron,
  NetworkAnalysisResult,
  SimulationResult,
  runNetworkAnalysis,
} from '../../api/client';

interface NetworkAnalysisPanelProps {
  neurons: Neuron[];
  selectedNeuron: Neuron | null;
  simulationResult: SimulationResult | null;
  onSelectNeuron: (neuron: Neuron | null) => void;
  analysisResult: NetworkAnalysisResult | null;
  onAnalysisResult: (result: NetworkAnalysisResult | null) => void;
  onGoToSimulation: () => void;
  highlightAffectedOnly: boolean;
  onToggleHighlightAffected: () => void;
  activeHopFilter: number | 'all';
  onSelectHopFilter: (hop: number | 'all') => void;
}

export const NetworkAnalysisPanel: React.FC<NetworkAnalysisPanelProps> = ({
  neurons,
  selectedNeuron,
  simulationResult,
  onSelectNeuron,
  analysisResult,
  onAnalysisResult,
  onGoToSimulation,
  highlightAffectedOnly,
  onToggleHighlightAffected,
  activeHopFilter,
  onSelectHopFilter,
}) => {
  const [threshold, setThreshold] = useState<number>(0.05);
  const [maxHops, setMaxHops] = useState<number>(3);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'summary' | 'structural' | 'affected' | 'targets' | 'centrality' | 'charts'>('summary');
  const [centralitySortBy, setCentralitySortBy] = useState<'betweenness' | 'in_degree' | 'out_degree' | 'closeness'>('betweenness');

  const neuronMap = useMemo(() => {
    const map = new Map<string, Neuron>();
    neurons.forEach(n => map.set(n.neuron_id, n));
    return map;
  }, [neurons]);

  const handleRunAnalysis = async () => {
    if (!simulationResult) return;
    try {
      setIsLoading(true);
      setError(null);
      const res = await runNetworkAnalysis({
        simulation_id: simulationResult.simulation_id,
        threshold: threshold,
        max_hops: maxHops,
      });
      onAnalysisResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compute network analysis');
    } finally {
      setIsLoading(false);
    }
  };

  // If no simulation has been run yet
  if (!simulationResult) {
    return (
      <div className="panel-section" style={{ textAlign: 'center', padding: '1.5rem 0.5rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.75rem', opacity: 0.6 }}>📊</div>
        <h3 style={{ color: '#f8fafc', fontSize: '1rem', marginBottom: '0.5rem' }}>
          Network Analysis Engine
        </h3>
        <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: 1.5, marginBottom: '1.25rem' }}>
          Run a neural perturbation simulation first. The analysis engine will calculate structural metrics,
          target reachability, and quantify model-affected activity propagation on the resulting subnetwork.
        </p>
        <button
          className="btn btn-primary"
          style={{ width: '100%', fontSize: '0.85rem' }}
          onClick={onGoToSimulation}
        >
          Go to Simulation Tab
        </button>
      </div>
    );
  }

  // Sorted centralities
  const sortedCentrality = analysisResult
    ? [...analysisResult.centrality].sort((a, b) => {
        if (centralitySortBy === 'betweenness') return b.betweenness_centrality - a.betweenness_centrality;
        if (centralitySortBy === 'in_degree') return b.in_degree_centrality - a.in_degree_centrality;
        if (centralitySortBy === 'out_degree') return b.out_degree_centrality - a.out_degree_centrality;
        return b.closeness_centrality - a.closeness_centrality;
      })
    : [];

  const selectedNeuronCentrality = selectedNeuron && analysisResult
    ? analysisResult.centrality.find(c => c.neuron_id === selectedNeuron.neuron_id)
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Header and Controls */}
      <div className="panel-section" style={{ paddingBottom: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
          <h2 className="panel-title" style={{ margin: 0, fontSize: '0.95rem', color: '#38bdf8' }}>
            Network Analysis
          </h2>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Phase 6</span>
        </div>

        {/* Scientific boundary disclaimer */}
        <div style={{
          backgroundColor: 'rgba(30, 41, 59, 0.7)',
          borderLeft: '3px solid #38bdf8',
          padding: '0.4rem 0.6rem',
          borderRadius: '2px',
          fontSize: '0.7rem',
          color: '#cbd5e1',
          lineHeight: 1.4,
          marginBottom: '0.75rem',
        }}>
          <strong>Scientific Principle:</strong> Network metrics describe the analyzed computational graph.
          They do not denote biological importance, in vivo firing, or physiological toxicity.
        </div>

        {/* Threshold and Hop depth configuration */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div>
            <label style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block', marginBottom: '0.2rem' }}>
              Delta Threshold (|Δ| ≥ θ):
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <input
                type="number"
                step="0.01"
                min="0.0"
                max="1.0"
                value={threshold}
                onChange={e => setThreshold(parseFloat(e.target.value) || 0.0)}
                style={{
                  width: '100%',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  padding: '0.25rem 0.4rem',
                  borderRadius: '3px',
                  fontSize: '0.75rem',
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block', marginBottom: '0.2rem' }}>
              Max Reachability Hops:
            </label>
            <select
              value={maxHops}
              onChange={e => setMaxHops(parseInt(e.target.value, 10))}
              style={{
                width: '100%',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                padding: '0.25rem 0.4rem',
                borderRadius: '3px',
                fontSize: '0.75rem',
              }}
            >
              <option value={1}>1 Hop</option>
              <option value={2}>2 Hops</option>
              <option value={3}>3 Hops</option>
              <option value={4}>4 Hops</option>
              <option value={5}>5 Hops</option>
            </select>
          </div>
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
          onClick={handleRunAnalysis}
          disabled={isLoading}
        >
          {isLoading ? 'Computing Analysis...' : (analysisResult ? 'Update Network Analysis' : 'Run Network Analysis')}
        </button>

        {error && (
          <div style={{ color: '#f87171', fontSize: '0.75rem', marginTop: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.4rem', borderRadius: '4px' }}>
            {error}
          </div>
        )}
      </div>

      {/* Analysis Sub-Navigation Tabs */}
      {analysisResult && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.25rem' }}>
            {[
              { id: 'summary', label: 'Summary' },
              { id: 'affected', label: 'Affected' },
              { id: 'structural', label: 'Structure' },
              { id: 'targets', label: 'Targets' },
              { id: 'centrality', label: 'Centrality' },
              { id: 'charts', label: 'Charts' },
            ].map(tab => (
              <button
                key={tab.id}
                className="btn"
                style={{
                  fontSize: '0.7rem',
                  padding: '0.3rem 0.2rem',
                  background: activeSection === tab.id ? '#1e293b' : 'transparent',
                  borderColor: activeSection === tab.id ? '#38bdf8' : '#334155',
                  color: activeSection === tab.id ? '#38bdf8' : '#94a3b8',
                }}
                onClick={() => setActiveSection(tab.id as any)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* 3D Visual Filters Bar */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            padding: '0.4rem 0.6rem',
            borderRadius: '4px',
            border: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.7rem',
          }}>
            <span style={{ color: '#cbd5e1' }}>3D Focus:</span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                className="btn"
                style={{
                  fontSize: '0.65rem',
                  padding: '0.2rem 0.4rem',
                  background: highlightAffectedOnly ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                  borderColor: highlightAffectedOnly ? '#38bdf8' : '#334155',
                  color: highlightAffectedOnly ? '#38bdf8' : '#94a3b8',
                }}
                onClick={onToggleHighlightAffected}
              >
                {highlightAffectedOnly ? '★ Model-Affected Highlighted' : 'Highlight Affected'}
              </button>
            </div>
          </div>

          {/* SECTION 1: Summary Overview */}
          {activeSection === 'summary' && (
            <div className="panel-section">
              <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Perturbation Propagation Overview
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginBottom: '0.6rem' }}>
                <div style={{ background: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
                  <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Model-Affected Neurons</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>
                    {analysisResult.perturbation_analysis.network_summary.model_affected_neuron_count}
                    <span style={{ fontSize: '0.7rem', fontWeight: 400, color: '#94a3b8', marginLeft: '0.3rem' }}>
                      ({(analysisResult.perturbation_analysis.network_summary.model_affected_neuron_fraction * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>

                <div style={{ background: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
                  <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Max Activity Shift</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>
                    {analysisResult.perturbation_analysis.network_summary.max_absolute_activity_change.toFixed(4)}
                  </div>
                </div>
              </div>

              <div className="data-row">
                <span className="data-label">Mean Activity Shift (|Δ|):</span>
                <span className="data-value">{analysisResult.perturbation_analysis.network_summary.mean_absolute_activity_change.toFixed(4)}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Total Network Δ Activity:</span>
                <span className="data-value" style={{
                  color: analysisResult.perturbation_analysis.network_summary.delta_total_activity >= 0 ? '#38bdf8' : '#c084fc'
                }}>
                  {analysisResult.perturbation_analysis.network_summary.delta_total_activity >= 0 ? '+' : ''}
                  {analysisResult.perturbation_analysis.network_summary.delta_total_activity.toFixed(4)}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Mean Baseline → Perturbed:</span>
                <span className="data-value">
                  {analysisResult.perturbation_analysis.network_summary.mean_baseline_activity.toFixed(4)} → {analysisResult.perturbation_analysis.network_summary.mean_perturbed_activity.toFixed(4)}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Target Count:</span>
                <span className="data-value">{analysisResult.perturbation_analysis.target_neuron_ids.length}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Threshold Applied:</span>
                <span className="data-value">{analysisResult.provenance.threshold}</span>
              </div>

              {/* Selected Neuron Quick Stats if any */}
              {selectedNeuron && (
                <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid #1e293b' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.3rem' }}>
                    Selected: {selectedNeuron.neuron_id}
                  </div>
                  {selectedNeuronCentrality ? (
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', lineHeight: 1.5 }}>
                      Betweenness: <span style={{ color: '#f8fafc' }}>{selectedNeuronCentrality.betweenness_centrality.toFixed(4)}</span> |
                      In-Cent: <span style={{ color: '#f8fafc' }}>{selectedNeuronCentrality.in_degree_centrality.toFixed(4)}</span> |
                      Out-Cent: <span style={{ color: '#f8fafc' }}>{selectedNeuronCentrality.out_degree_centrality.toFixed(4)}</span>
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.7rem', color: '#64748b' }}>No centrality calculated</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* SECTION 2: Model-Affected Neurons List */}
          {activeSection === 'affected' && (
            <div className="panel-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0, textTransform: 'uppercase' }}>
                  Model-Affected Neurons (|Δ| ≥ {threshold})
                </h3>
                <span style={{ fontSize: '0.7rem', color: '#38bdf8' }}>
                  {analysisResult.perturbation_analysis.affected_neurons.filter(n => n.exceeds_threshold).length} neurons
                </span>
              </div>

              <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1px solid #1e293b', borderRadius: '4px' }}>
                <table style={{ width: '100%', fontSize: '0.7rem', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ background: '#0f172a', position: 'sticky', top: 0, zIndex: 2 }}>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Neuron ID</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Base</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Pert</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Δ</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Hop</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResult.perturbation_analysis.affected_neurons.map(neuron => {
                      const isSel = selectedNeuron?.neuron_id === neuron.neuron_id;
                      return (
                        <tr
                          key={neuron.neuron_id}
                          onClick={() => {
                            const found = neuronMap.get(neuron.neuron_id);
                            if (found) onSelectNeuron(found);
                          }}
                          style={{
                            cursor: 'pointer',
                            background: isSel ? 'rgba(56, 189, 248, 0.15)' : neuron.exceeds_threshold ? 'rgba(15, 23, 42, 0.4)' : 'transparent',
                            color: neuron.exceeds_threshold ? '#f8fafc' : '#64748b',
                            borderBottom: '1px solid #1e293b',
                          }}
                        >
                          <td style={{ padding: '0.3rem 0.4rem', fontFamily: 'monospace' }}>
                            {neuron.is_target && <span style={{ color: '#f59e0b', marginRight: '0.2rem' }}>★</span>}
                            {neuron.neuron_id}
                          </td>
                          <td style={{ padding: '0.3rem 0.4rem' }}>{neuron.baseline_activity.toFixed(2)}</td>
                          <td style={{ padding: '0.3rem 0.4rem' }}>{neuron.perturbed_activity.toFixed(2)}</td>
                          <td style={{
                            padding: '0.3rem 0.4rem',
                            fontWeight: neuron.exceeds_threshold ? 600 : 400,
                            color: neuron.delta_activity > 0 ? '#38bdf8' : neuron.delta_activity < 0 ? '#c084fc' : '#94a3b8',
                          }}>
                            {neuron.delta_activity > 0 ? `+${neuron.delta_activity.toFixed(3)}` : neuron.delta_activity.toFixed(3)}
                          </td>
                          <td style={{ padding: '0.3rem 0.4rem' }}>{neuron.hop_distance !== null && neuron.hop_distance !== undefined ? neuron.hop_distance : '—'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 3: Structural Graph Metrics */}
          {activeSection === 'structural' && (
            <div className="panel-section">
              <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Connectome Subgraph Topology
              </h3>

              <div className="data-row">
                <span className="data-label">Neurons:</span>
                <span className="data-value">{analysisResult.network_metrics.neuron_count}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Directed Connections:</span>
                <span className="data-value">{analysisResult.network_metrics.connection_count}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Graph Density:</span>
                <span className="data-value">{analysisResult.network_metrics.density.toFixed(5)}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Mean In / Out Degree:</span>
                <span className="data-value">
                  {analysisResult.network_metrics.mean_in_degree.toFixed(2)} / {analysisResult.network_metrics.mean_out_degree.toFixed(2)}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Max In / Out Degree:</span>
                <span className="data-value">
                  {analysisResult.network_metrics.max_in_degree} / {analysisResult.network_metrics.max_out_degree}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Weakly Connected Components:</span>
                <span className="data-value">{analysisResult.network_metrics.weakly_connected_components}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Strongly Connected Components:</span>
                <span className="data-value">{analysisResult.network_metrics.strongly_connected_components}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Largest WCC Node Count:</span>
                <span className="data-value">{analysisResult.network_metrics.largest_wcc_size}</span>
              </div>
              <div className="data-row">
                <span className="data-label">Average Shortest Path:</span>
                <span className="data-value">
                  {analysisResult.network_metrics.average_shortest_path_length != null
                    ? analysisResult.network_metrics.average_shortest_path_length.toFixed(3)
                    : 'N/A (disconnected)'}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Directed Acyclic (DAG):</span>
                <span className="data-value">{analysisResult.network_metrics.is_dag ? 'Yes' : 'No'}</span>
              </div>
            </div>
          )}

          {/* SECTION 4: Target-Centered Reachability */}
          {activeSection === 'targets' && (
            <div className="panel-section">
              <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Target Reachability & Paths
              </h3>

              {analysisResult.target_analysis.length === 0 ? (
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', textAlign: 'center', padding: '1rem' }}>
                  No perturbation targets defined in simulation.
                </div>
              ) : (
                analysisResult.target_analysis.map(target => (
                  <div
                    key={target.target_neuron_id}
                    style={{
                      background: '#0f172a',
                      padding: '0.6rem',
                      borderRadius: '4px',
                      border: '1px solid #1e293b',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                      <span style={{ fontWeight: 600, color: '#f59e0b', fontSize: '0.8rem' }}>
                        ★ Target: {target.target_neuron_id}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                        Deg: {target.total_degree} (In: {target.in_degree}, Out: {target.out_degree})
                      </span>
                    </div>

                    <div className="data-row" style={{ fontSize: '0.7rem' }}>
                      <span className="data-label">Upstream Pre-synaptic:</span>
                      <span className="data-value">{target.upstream_neuron_count} partners</span>
                    </div>
                    <div className="data-row" style={{ fontSize: '0.7rem' }}>
                      <span className="data-label">Downstream Post-synaptic:</span>
                      <span className="data-value">{target.downstream_neuron_count} partners</span>
                    </div>

                    {/* Multi-hop breakdown */}
                    <div style={{ marginTop: '0.4rem', borderTop: '1px solid #1e293b', paddingTop: '0.3rem' }}>
                      <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginBottom: '0.2rem' }}>
                        Downstream Reachability by Layer:
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {Object.entries(target.reachability_counts).map(([hopStr, count]) => {
                          const hopNum = parseInt(hopStr, 10);
                          const isHopActive = activeHopFilter === hopNum;
                          return (
                            <button
                              key={hopStr}
                              className="btn"
                              style={{
                                flex: 1,
                                background: isHopActive ? 'rgba(56, 189, 248, 0.25)' : '#1e293b',
                                borderColor: isHopActive ? '#38bdf8' : '#334155',
                                padding: '0.25rem',
                                borderRadius: '3px',
                                textAlign: 'center',
                                cursor: 'pointer',
                              }}
                              onClick={() => onSelectHopFilter(isHopActive ? 'all' : hopNum)}
                            >
                              <div style={{ fontSize: '0.6rem', color: isHopActive ? '#38bdf8' : '#94a3b8' }}>Hop {hopStr}</div>
                              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: isHopActive ? '#38bdf8' : '#cbd5e1' }}>{count}</div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* SECTION 5: Centrality Ranking */}
          {activeSection === 'centrality' && (
            <div className="panel-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0, textTransform: 'uppercase' }}>
                  Network Centrality
                </h3>
                <select
                  value={centralitySortBy}
                  onChange={e => setCentralitySortBy(e.target.value as any)}
                  style={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    color: '#f8fafc',
                    fontSize: '0.65rem',
                    padding: '0.15rem 0.3rem',
                    borderRadius: '3px',
                  }}
                >
                  <option value="betweenness">Sort: Betweenness</option>
                  <option value="in_degree">Sort: In-Degree</option>
                  <option value="out_degree">Sort: Out-Degree</option>
                  <option value="closeness">Sort: Closeness</option>
                </select>
              </div>

              <div style={{ fontSize: '0.65rem', color: '#64748b', marginBottom: '0.4rem', fontStyle: 'italic' }}>
                Highest modeled network centrality in the analyzed subgraph:
              </div>

              <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1px solid #1e293b', borderRadius: '4px' }}>
                <table style={{ width: '100%', fontSize: '0.7rem', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ background: '#0f172a', position: 'sticky', top: 0, zIndex: 2 }}>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Neuron</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Betweenness</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>In-Cent</th>
                      <th style={{ padding: '0.3rem 0.4rem' }}>Out-Cent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedCentrality.slice(0, 25).map(c => {
                      const isSel = selectedNeuron?.neuron_id === c.neuron_id;
                      return (
                        <tr
                          key={c.neuron_id}
                          onClick={() => {
                            const found = neuronMap.get(c.neuron_id);
                            if (found) onSelectNeuron(found);
                          }}
                          style={{
                            cursor: 'pointer',
                            background: isSel ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                            borderBottom: '1px solid #1e293b',
                          }}
                        >
                          <td style={{ padding: '0.3rem 0.4rem', fontFamily: 'monospace', color: isSel ? '#38bdf8' : '#f8fafc' }}>
                            {c.neuron_id}
                          </td>
                          <td style={{ padding: '0.3rem 0.4rem', fontWeight: 600, color: '#f59e0b' }}>
                            {c.betweenness_centrality.toFixed(4)}
                          </td>
                          <td style={{ padding: '0.3rem 0.4rem', color: '#94a3b8' }}>
                            {c.in_degree_centrality.toFixed(3)}
                          </td>
                          <td style={{ padding: '0.3rem 0.4rem', color: '#94a3b8' }}>
                            {c.out_degree_centrality.toFixed(3)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 6: Lightweight SVG Charts */}
          {activeSection === 'charts' && (
            <div className="panel-section">
              <h3 style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Analytical Charts
              </h3>

              {/* Chart 1: Activity Delta Distribution */}
              <div style={{ background: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b', marginBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#f8fafc', fontWeight: 600, marginBottom: '0.3rem' }}>
                  Activity Change Distribution (|Δ|)
                </div>
                {(() => {
                  const deltas = analysisResult.perturbation_analysis.affected_neurons.map(n => n.absolute_delta);
                  const bins = [0, 0.05, 0.1, 0.2, 0.4, 1.0];
                  const counts = [0, 0, 0, 0, 0];
                  deltas.forEach(d => {
                    for (let i = 0; i < bins.length - 1; i++) {
                      if (d >= bins[i] && d < bins[i + 1]) {
                        counts[i]++;
                        break;
                      }
                      if (i === bins.length - 2 && d >= bins[i + 1]) {
                        counts[i]++;
                      }
                    }
                  });
                  const maxCount = Math.max(...counts, 1);

                  return (
                    <div style={{ display: 'flex', alignItems: 'flex-end', height: '60px', gap: '4px', paddingTop: '10px' }}>
                      {counts.map((cnt, idx) => {
                        const h = (cnt / maxCount) * 50;
                        const label = `<${bins[idx + 1]}`;
                        return (
                          <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.6rem', color: '#94a3b8', marginBottom: '2px' }}>{cnt}</span>
                            <div style={{
                              width: '100%',
                              height: `${Math.max(h, 4)}px`,
                              backgroundColor: idx === 0 ? '#475569' : '#38bdf8',
                              borderRadius: '2px 2px 0 0',
                            }} />
                            <span style={{ fontSize: '0.55rem', color: '#64748b', marginTop: '2px' }}>{label}</span>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>

              {/* Chart 2: Baseline vs Perturbed Network Activity */}
              <div style={{ background: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
                <div style={{ fontSize: '0.7rem', color: '#f8fafc', fontWeight: 600, marginBottom: '0.3rem' }}>
                  Network Modeled Activity Shift
                </div>
                {(() => {
                  const baseMean = analysisResult.perturbation_analysis.network_summary.mean_baseline_activity;
                  const pertMean = analysisResult.perturbation_analysis.network_summary.mean_perturbed_activity;
                  const maxVal = Math.max(baseMean, pertMean, 0.5);

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', paddingTop: '0.2rem' }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#94a3b8' }}>
                          <span>Baseline Mean:</span>
                          <span style={{ color: '#f8fafc' }}>{baseMean.toFixed(3)}</span>
                        </div>
                        <div style={{ height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ width: `${(baseMean / maxVal) * 100}%`, height: '100%', background: '#64748b' }} />
                        </div>
                      </div>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#94a3b8' }}>
                          <span>Perturbed Mean:</span>
                          <span style={{ color: '#38bdf8' }}>{pertMean.toFixed(3)}</span>
                        </div>
                        <div style={{ height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ width: `${(pertMean / maxVal) * 100}%`, height: '100%', background: '#38bdf8' }} />
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Provenance footer */}
          <div style={{ fontSize: '0.65rem', color: '#64748b', padding: '0.3rem 0.5rem', borderTop: '1px solid #1e293b' }}>
            Provenance: {analysisResult.provenance.dataset_name || 'synthetic'} • sim: {analysisResult.simulation_id.slice(0, 10)}... • ver: {analysisResult.provenance.analysis_version}
          </div>
        </>
      )}
    </div>
  );
};
