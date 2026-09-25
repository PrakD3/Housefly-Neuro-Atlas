import React from 'react';
import { Neuron, ConnectomeMetadata } from '../../api/client';

interface UIOverlayProps {
  metadata: ConnectomeMetadata | null;
  selectedNeuron: Neuron | null;
  hoveredNeuron: Neuron | null;
  showConnections: boolean;
  onToggleConnections: () => void;
  onResetCamera: () => void;
}

export const UIOverlay: React.FC<UIOverlayProps> = ({
  metadata,
  selectedNeuron,
  hoveredNeuron,
  showConnections,
  onToggleConnections,
  onResetCamera
}) => {
  const displayNeuron = selectedNeuron || hoveredNeuron;

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '1rem',
      color: 'white',
      fontFamily: 'sans-serif'
    }}>
      
      {/* Top Bar: Warning Label and Metadata */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          {metadata && metadata.is_synthetic && (
            <div style={{ 
              backgroundColor: 'rgba(239, 68, 68, 0.8)', 
              padding: '0.5rem 1rem', 
              borderRadius: '0.25rem',
              fontWeight: 'bold',
              marginBottom: '0.5rem',
              display: 'inline-block'
            }}>
              SYNTHETIC CONNECTOME — SOFTWARE TEST DATA
            </div>
          )}
          {metadata && (
            <div style={{ backgroundColor: 'rgba(0,0,0,0.5)', padding: '0.5rem', borderRadius: '0.25rem' }}>
              <p style={{ margin: 0 }}>Nodes: {metadata.neuron_count}</p>
              <p style={{ margin: 0 }}>Edges: {metadata.connection_count}</p>
            </div>
          )}
        </div>
        
        {/* Controls */}
        <div style={{ 
          pointerEvents: 'auto', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '0.5rem',
          backgroundColor: 'rgba(0,0,0,0.5)', 
          padding: '0.5rem', 
          borderRadius: '0.25rem' 
        }}>
          <button 
            onClick={onToggleConnections}
            style={{ padding: '0.5rem', cursor: 'pointer', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '0.25rem' }}
          >
            {showConnections ? "Hide Connections" : "Show Connections"}
          </button>
          <button 
            onClick={onResetCamera}
            style={{ padding: '0.5rem', cursor: 'pointer', background: '#4b5563', color: 'white', border: 'none', borderRadius: '0.25rem' }}
          >
            Reset Camera
          </button>
        </div>
      </div>

      {/* Bottom Bar: Neuron Details */}
      <div style={{ alignSelf: 'flex-start' }}>
        {displayNeuron && (
          <div style={{ 
            backgroundColor: 'rgba(15, 23, 42, 0.9)', 
            padding: '1rem', 
            borderRadius: '0.5rem',
            border: '1px solid #334155',
            minWidth: '250px'
          }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#60a5fa' }}>{displayNeuron.neuron_id}</h3>
            <p style={{ margin: '0.25rem 0' }}><strong>Type:</strong> {displayNeuron.cell_type}</p>
            <p style={{ margin: '0.25rem 0' }}><strong>Region:</strong> {displayNeuron.region}</p>
            <p style={{ margin: '0.25rem 0', fontSize: '0.8rem', color: '#94a3b8' }}>
              {displayNeuron.has_coordinates
                ? `pos: (${displayNeuron.x!.toFixed(1)}, ${displayNeuron.y!.toFixed(1)}, ${displayNeuron.z!.toFixed(1)})`
                : 'pos: no spatial data'}
            </p>
          </div>
        )}
      </div>

    </div>
  );
};
