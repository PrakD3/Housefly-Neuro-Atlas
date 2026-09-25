import React, { useState } from 'react';

export interface RealModePanelProps {
  onLoadNeighborhood: (neuronId: string, hops: number) => void;
  onClear: () => void;
  isLoading: boolean;
  activeNeuronId?: string | null;
}

export const RealModePanel: React.FC<RealModePanelProps> = ({
  onLoadNeighborhood,
  onClear,
  isLoading,
  activeNeuronId,
}) => {
  const [inputId, setInputId] = useState('');
  const [hops, setHops] = useState<number>(1);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputId.trim();
    if (trimmed) {
      onLoadNeighborhood(trimmed, hops);
    }
  };

  return (
    <div className="panel-section">
      <h2 className="panel-title">Real Connectome Query</h2>
      <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '0 0 0.75rem 0', lineHeight: 1.4 }}>
        Enter a neuPrint neuron body ID to load a bounded subnetwork from the dataset.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div className="control-group">
          <label htmlFor="real-neuron-input">Neuron Body ID</label>
          <input
            id="real-neuron-input"
            type="text"
            placeholder="e.g. 720575940614131"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="control-group">
          <label htmlFor="hops-select">Expansion Depth (Hops)</label>
          <select
            id="hops-select"
            value={hops}
            onChange={(e) => setHops(Number(e.target.value))}
            disabled={isLoading}
          >
            <option value={1}>1 Hop (Direct Neighbors)</option>
            <option value={2}>2 Hops (Local Subnetwork)</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ flex: 1 }}
            disabled={isLoading || !inputId.trim()}
          >
            {isLoading ? 'Loading Subgraph...' : 'Load Subgraph'}
          </button>
          {activeNeuronId && (
            <button
              type="button"
              className="btn"
              onClick={() => {
                setInputId('');
                onClear();
              }}
              disabled={isLoading}
            >
              Clear
            </button>
          )}
        </div>
      </form>

      {activeNeuronId && (
        <div style={{ marginTop: '0.75rem', padding: '0.5rem', backgroundColor: '#1e293b', borderRadius: '4px', fontSize: '0.75rem', color: '#94a3b8' }}>
          <span>Current Focal Neuron: </span>
          <strong style={{ color: '#38bdf8' }}>{activeNeuronId}</strong>
        </div>
      )}
    </div>
  );
};
