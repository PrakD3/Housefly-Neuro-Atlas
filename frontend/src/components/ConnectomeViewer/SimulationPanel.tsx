import React, { useState, useMemo } from 'react';
import { 
  Neuron, 
  NeuralPerturbation, 
  PerturbationEffect, 
  SimulationResult, 
  runSimulation 
} from '../../api/client';

interface SimulationPanelProps {
  neurons: Neuron[];
  selectedNeuron: Neuron | null;
  activeFocalId: string | null;
  isRealMode: boolean;
  onSelectNeuron: (neuron: Neuron | null) => void;
  onSimulationResult: (result: SimulationResult | null) => void;
  onSimulationModeChange: (mode: 'none' | 'perturbed' | 'baseline' | 'delta') => void;
  onTimeStepChange: (stepIndex: number) => void;
  simulationResult: SimulationResult | null;
  currentStepIndex: number;
  simMode: 'none' | 'perturbed' | 'baseline' | 'delta';
  isPlaying: boolean;
  onTogglePlay: () => void;
}

export const SimulationPanel: React.FC<SimulationPanelProps> = ({
  neurons,
  selectedNeuron,
  activeFocalId,
  isRealMode,
  onSelectNeuron,
  onSimulationResult,
  onSimulationModeChange,
  onTimeStepChange,
  simulationResult,
  currentStepIndex,
  simMode,
  isPlaying,
  onTogglePlay,
}) => {
  const [targetId, setTargetId] = useState<string>(
    selectedNeuron?.neuron_id || activeFocalId || (neurons[0]?.neuron_id ?? '')
  );
  const [effect, setEffect] = useState<PerturbationEffect>('activation');
  const [magnitude, setMagnitude] = useState<number>(0.5);
  const [duration, setDuration] = useState<number>(3.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync target when selected neuron changes if no custom target is typed
  const handleUseSelectedNeuron = () => {
    if (selectedNeuron) {
      setTargetId(selectedNeuron.neuron_id);
    }
  };

  const handleRunSimulation = async () => {
    if (!targetId.trim()) {
      setError("Please specify a target neuron ID.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const perturbation: NeuralPerturbation = {
        target_neuron_ids: [targetId.trim()],
        effect,
        magnitude,
        start_time: 0.0,
        duration,
        mechanism: "computational_test",
        source: "user_defined",
        confidence: "unspecified",
      };

      const neuronIds = neurons.map(n => n.neuron_id);

      const result = await runSimulation({
        neuron_ids: isRealMode ? neuronIds : (neuronIds.length <= 500 ? neuronIds : undefined),
        focal_neuron_id: isRealMode && activeFocalId ? activeFocalId : undefined,
        hops: 1,
        perturbations: [perturbation],
        config: {
          dt: 0.1,
          duration,
          decay: 0.85,
          propagation_strength: 0.5,
          baseline_activity: 0.2,
        },
      });

      onSimulationResult(result);
      onSimulationModeChange('perturbed');
      onTimeStepChange(result.time_series.length - 1);
    } catch (err: any) {
      setError(err.message || "Failed to execute simulation.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    onSimulationResult(null);
    onSimulationModeChange('none');
    onTimeStepChange(0);
    setError(null);
  };

  // Find target neuron metadata for display
  const targetNeuronMeta = useMemo(() => {
    return neurons.find(n => n.neuron_id === targetId);
  }, [neurons, targetId]);

  const currentStepTime = useMemo(() => {
    if (!simulationResult || !simulationResult.time_series[currentStepIndex]) {
      return 0.0;
    }
    return simulationResult.time_series[currentStepIndex].time;
  }, [simulationResult, currentStepIndex]);

  return (
    <div className="simulation-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Explicit Scientific Status Banner */}
      <div style={{
        backgroundColor: 'rgba(30, 41, 59, 0.95)',
        border: '1px solid #0284c7',
        borderRadius: '6px',
        padding: '0.75rem',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: '#38bdf8',
          fontSize: '0.75rem',
          fontWeight: 700,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginBottom: '0.25rem',
        }}>
          <span>⚡</span>
          <span>Computational Simulation</span>
        </div>
        <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.4 }}>
          Normalized model activity ∈ [0, 1]. Discrete-time graph model for testing network perturbation.
          Does not simulate biological electrophysiology or toxicity.
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '4px',
          padding: '0.5rem 0.75rem',
          color: '#fca5a5',
          fontSize: '0.8rem',
        }}>
          {error}
        </div>
      )}

      {/* Target Neuron Selection */}
      <div className="control-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
          <label htmlFor="sim-target-id" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Target Neuron ID</label>
          {selectedNeuron && selectedNeuron.neuron_id !== targetId && (
            <button
              onClick={handleUseSelectedNeuron}
              style={{
                background: 'none',
                border: 'none',
                color: '#38bdf8',
                fontSize: '0.75rem',
                cursor: 'pointer',
                padding: 0,
                textDecoration: 'underline',
              }}
            >
              Use Selected ({selectedNeuron.neuron_id})
            </button>
          )}
        </div>
        <input
          id="sim-target-id"
          type="text"
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          placeholder="e.g. syn_neuron_0 or body ID"
          style={{ width: '100%', boxSizing: 'border-box' }}
        />
        {targetNeuronMeta && (
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            Type: {targetNeuronMeta.cell_type} | Region: {targetNeuronMeta.region}
          </div>
        )}
      </div>

      {/* Perturbation Effect */}
      <div className="control-group">
        <label htmlFor="sim-effect" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Perturbation Effect</label>
        <select
          id="sim-effect"
          value={effect}
          onChange={(e) => setEffect(e.target.value as PerturbationEffect)}
          style={{ width: '100%', boxSizing: 'border-box' }}
        >
          <option value="activation">Activation (+ activity)</option>
          <option value="excitation">Excitation (+ activity, equivalent)</option>
          <option value="inhibition">Inhibition (- activity)</option>
          <option value="suppression">Suppression (- activity, equivalent)</option>
        </select>
        <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem', lineHeight: 1.3 }}>
          Computational equivalence: Activation/Excitation add positive modeled activity; Inhibition/Suppression subtract modeled activity.
        </div>
      </div>

      {/* Magnitude Slider */}
      <div className="control-group">
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <label htmlFor="sim-magnitude" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Model Magnitude</label>
          <span style={{ fontSize: '0.8rem', color: '#38bdf8' }}>{magnitude.toFixed(2)}</span>
        </div>
        <input
          id="sim-magnitude"
          type="range"
          min="0.05"
          max="1.0"
          step="0.05"
          value={magnitude}
          onChange={(e) => setMagnitude(parseFloat(e.target.value))}
        />
      </div>

      {/* Duration Slider */}
      <div className="control-group">
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <label htmlFor="sim-duration" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Duration (s)</label>
          <span style={{ fontSize: '0.8rem', color: '#38bdf8' }}>{duration.toFixed(1)}s</span>
        </div>
        <input
          id="sim-duration"
          type="range"
          min="0.5"
          max="10.0"
          step="0.5"
          value={duration}
          onChange={(e) => setDuration(parseFloat(e.target.value))}
        />
      </div>

      {/* Run & Reset Actions */}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
        <button
          className="btn btn-primary"
          style={{ flex: 1, padding: '0.5rem' }}
          onClick={handleRunSimulation}
          disabled={loading || neurons.length === 0}
        >
          {loading ? "Simulating..." : "Run Simulation"}
        </button>
        {simulationResult && (
          <button
            className="btn"
            style={{ padding: '0.5rem' }}
            onClick={handleReset}
          >
            Reset
          </button>
        )}
      </div>

      {/* Simulation Results Display */}
      {simulationResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
          {/* View Mode Tabs */}
          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
              Visualization Mode (3D View):
            </div>
            <div style={{ display: 'flex', gap: '0.25rem', background: '#0f172a', padding: '0.25rem', borderRadius: '4px' }}>
              <button
                style={{
                  flex: 1,
                  padding: '0.35rem 0.2rem',
                  fontSize: '0.7rem',
                  background: simMode === 'perturbed' ? '#0284c7' : 'transparent',
                  color: simMode === 'perturbed' ? 'white' : '#94a3b8',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                }}
                onClick={() => onSimulationModeChange('perturbed')}
              >
                Perturbed
              </button>
              <button
                style={{
                  flex: 1,
                  padding: '0.35rem 0.2rem',
                  fontSize: '0.7rem',
                  background: simMode === 'baseline' ? '#0284c7' : 'transparent',
                  color: simMode === 'baseline' ? 'white' : '#94a3b8',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                }}
                onClick={() => onSimulationModeChange('baseline')}
              >
                Baseline
              </button>
              <button
                style={{
                  flex: 1,
                  padding: '0.35rem 0.2rem',
                  fontSize: '0.7rem',
                  background: simMode === 'delta' ? '#0284c7' : 'transparent',
                  color: simMode === 'delta' ? 'white' : '#94a3b8',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                }}
                onClick={() => onSimulationModeChange('delta')}
              >
                Δ Activity
              </button>
            </div>
          </div>

          {/* Timeline Scrubber */}
          <div style={{ background: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <button
                onClick={onTogglePlay}
                style={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  color: 'white',
                  borderRadius: '3px',
                  padding: '0.2rem 0.5rem',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                {isPlaying ? "⏸ Pause" : "▶ Play"}
              </button>
              <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>
                t = {currentStepTime.toFixed(1)}s / {(simulationResult.config.duration ?? duration).toFixed(1)}s
              </span>
            </div>
            <input
              type="range"
              min="0"
              max={simulationResult.time_series.length - 1}
              value={currentStepIndex}
              onChange={(e) => onTimeStepChange(parseInt(e.target.value, 10))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Network Metrics Card */}
          <div className="panel-section" style={{ background: '#0f172a', padding: '0.75rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
            <h3 style={{ fontSize: '0.8rem', color: '#e2e8f0', margin: '0 0 0.5rem 0' }}>
              Network-Level Metrics
            </h3>
            <div className="data-row">
              <span className="data-label">Mean Activity</span>
              <span className="data-value">{simulationResult.metrics.mean_activity.toFixed(3)}</span>
            </div>
            <div className="data-row">
              <span className="data-label">Active Neurons</span>
              <span className="data-value">{simulationResult.metrics.active_neuron_count} / {neurons.length}</span>
            </div>
            <div className="data-row">
              <span className="data-label">Max / Min Activity</span>
              <span className="data-value">{simulationResult.metrics.maximum_activity.toFixed(2)} / {simulationResult.metrics.minimum_activity.toFixed(2)}</span>
            </div>
            <div className="data-row">
              <span className="data-label">Total Network Activity</span>
              <span className="data-value">{simulationResult.metrics.total_network_activity.toFixed(2)}</span>
            </div>
            <div className="data-row">
              <span className="data-label">Affected Neurons</span>
              <span className="data-value" style={{ color: '#38bdf8' }}>
                {simulationResult.metrics.downstream_affected_neuron_count}
              </span>
            </div>
          </div>

          {/* Top Affected Neurons List */}
          <div className="panel-section">
            <h3 style={{ fontSize: '0.8rem', color: '#e2e8f0', margin: '0 0 0.25rem 0' }}>
              Neuron Activity Comparison (Top Δ)
            </h3>
            <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {simulationResult.neuron_deltas.slice(0, 15).map((delta) => {
                const isSelected = selectedNeuron?.neuron_id === delta.neuron_id;
                const isTargetNode = delta.neuron_id === targetId;
                const deltaColor = delta.delta_activity > 0 ? '#38bdf8' : delta.delta_activity < 0 ? '#c084fc' : '#94a3b8';
                
                return (
                  <div
                    key={delta.neuron_id}
                    onClick={() => {
                      const match = neurons.find(n => n.neuron_id === delta.neuron_id);
                      if (match) onSelectNeuron(match);
                    }}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.35rem 0.5rem',
                      background: isSelected ? 'rgba(56, 189, 248, 0.15)' : '#0f172a',
                      border: isSelected ? '1px solid #38bdf8' : '1px solid #1e293b',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                    }}
                  >
                    <div>
                      <span style={{ color: isTargetNode ? '#f59e0b' : '#e2e8f0', fontWeight: isTargetNode ? 700 : 400 }}>
                        {delta.neuron_id}
                      </span>
                      {isTargetNode && <span style={{ color: '#f59e0b', fontSize: '0.65rem', marginLeft: '0.25rem' }}>[TARGET]</span>}
                      <span style={{ color: '#64748b', marginLeft: '0.4rem', fontSize: '0.7rem' }}>
                        Hop: {delta.hop_distance !== null ? delta.hop_distance : '∞'}
                      </span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ color: deltaColor, fontWeight: 600 }}>
                        {delta.delta_activity >= 0 ? `+${delta.delta_activity.toFixed(3)}` : delta.delta_activity.toFixed(3)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Provenance Footer */}
          <div style={{ fontSize: '0.65rem', color: '#64748b', borderTop: '1px solid #1e293b', paddingTop: '0.5rem' }}>
            <div>ID: {simulationResult.provenance.simulation_id}</div>
            <div>
              Dataset: {simulationResult.provenance.dataset_name} ({simulationResult.provenance.is_synthetic ? 'Synthetic' : 'Real'})
            </div>
            <div>Model: {simulationResult.provenance.model_version}</div>
          </div>
        </div>
      )}
    </div>
  );
};
