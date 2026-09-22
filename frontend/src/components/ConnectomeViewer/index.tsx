import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { 
  getConnectomeInfo, 
  getNeurons, 
  getNeuronNeighbors,
  Neuron, 
  Connection, 
  ConnectomeMetadata, 
  SubgraphResponse 
} from '../../api/client';
import { Scene } from './Scene';
import { UIOverlay } from './UIOverlay';

export const ConnectomeViewer: React.FC = () => {
  const [metadata, setMetadata] = useState<ConnectomeMetadata | null>(null);
  const [neurons, setNeurons] = useState<Neuron[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedNeuron, setSelectedNeuron] = useState<Neuron | null>(null);
  const [hoveredNeuron, setHoveredNeuron] = useState<Neuron | null>(null);
  const [neighborsData, setNeighborsData] = useState<SubgraphResponse | null>(null);
  const [showConnections, setShowConnections] = useState<boolean>(true);

  // We need a key to force re-render the canvas for resetting camera
  const [canvasKey, setCanvasKey] = useState<number>(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const info = await getConnectomeInfo();
        setMetadata(info);

        const allNeurons = await getNeurons();
        setNeurons(allNeurons);
        
        // For the synthetic graph, we can optionally fetch all connections by fetching subgraph of all neurons
        // But to keep it light, maybe we only show connections related to the selected neuron?
        // Actually, the requirements say "toggle connections on/off". Let's fetch all connections if it's small,
        // or just fetch neighbors on select.
        // For Phase 2, we will fetch neighbors dynamically when selected.
        setLoading(false);
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    const fetchNeighbors = async () => {
      if (selectedNeuron) {
        try {
          const data = await getNeuronNeighbors(selectedNeuron.neuron_id, 1);
          setNeighborsData(data);
          
          // For synthetic visual, if we don't have global connections loaded, 
          // let's at least populate the local connections to render
          setConnections(data.connections);
        } catch (err) {
          console.error("Failed to fetch neighbors", err);
        }
      } else {
        setNeighborsData(null);
        setConnections([]);
      }
    };
    
    fetchNeighbors();
  }, [selectedNeuron]);

  const handleSelectNeuron = useCallback((neuron: Neuron | null) => {
    setSelectedNeuron(prev => (prev?.neuron_id === neuron?.neuron_id ? null : neuron));
  }, []);

  const handleHoverNeuron = useCallback((neuron: Neuron | null) => {
    setHoveredNeuron(neuron);
  }, []);

  const toggleConnections = useCallback(() => {
    setShowConnections(prev => !prev);
  }, []);

  const resetCamera = useCallback(() => {
    setCanvasKey(prev => prev + 1);
  }, []);

  if (loading) return <div style={{ color: 'white', padding: '2rem' }}>Loading Connectome Data...</div>;
  if (error) return <div style={{ color: '#ef4444', padding: '2rem' }}>Error loading data: {error}</div>;

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#0f172a' }}>
      <Canvas key={canvasKey} camera={{ position: [0, 0, 25], fov: 60 }}>
        <Scene
          neurons={neurons}
          connections={connections}
          neighborsData={neighborsData}
          selectedNeuron={selectedNeuron}
          showConnections={showConnections}
          onSelectNeuron={handleSelectNeuron}
          onHoverNeuron={handleHoverNeuron}
        />
      </Canvas>
      <UIOverlay
        metadata={metadata}
        selectedNeuron={selectedNeuron}
        hoveredNeuron={hoveredNeuron}
        showConnections={showConnections}
        onToggleConnections={toggleConnections}
        onResetCamera={resetCamera}
      />
    </div>
  );
};
