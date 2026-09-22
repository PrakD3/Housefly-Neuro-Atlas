import React, { useMemo, useRef } from 'react';
import { OrbitControls, Stars } from '@react-three/drei';
import { Neuron, Connection, SubgraphResponse } from '../../api/client';
import { NeuronNode } from './NeuronNode';
import { ConnectionLine } from './ConnectionLine';

interface SceneProps {
  neurons: Neuron[];
  connections: Connection[];
  neighborsData: SubgraphResponse | null;
  selectedNeuron: Neuron | null;
  showConnections: boolean;
  onSelectNeuron: (neuron: Neuron | null) => void;
  onHoverNeuron: (neuron: Neuron | null) => void;
}

export const Scene: React.FC<SceneProps> = ({ 
  neurons, 
  connections, 
  neighborsData, 
  selectedNeuron, 
  showConnections,
  onSelectNeuron, 
  onHoverNeuron 
}) => {
  const controlsRef = useRef<any>(null);

  // Quick lookup maps
  const neuronMap = useMemo(() => {
    const map = new Map<string, Neuron>();
    neurons.forEach(n => map.set(n.neuron_id, n));
    return map;
  }, [neurons]);
  
  // Highlighted IDs from neighbors
  const highlightedNeuronIds = useMemo(() => {
    if (!neighborsData) return new Set<string>();
    return new Set(neighborsData.neurons.map(n => n.neuron_id));
  }, [neighborsData]);

  return (
    <>
      <color attach="background" args={['#0f172a']} />
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      
      {/* Neurons */}
      {neurons.map(neuron => (
        <NeuronNode
          key={neuron.neuron_id}
          neuron={neuron}
          isSelected={selectedNeuron?.neuron_id === neuron.neuron_id || highlightedNeuronIds.has(neuron.neuron_id)}
          onSelect={onSelectNeuron}
          onHover={onHoverNeuron}
        />
      ))}
      
      {/* Connections */}
      {showConnections && connections.map((conn, idx) => {
        const source = neuronMap.get(conn.source_neuron);
        const target = neuronMap.get(conn.target_neuron);
        
        if (!source || !target) return null;
        
        // Highlight connection if it's connected to the selected neuron
        const isHighlighted = selectedNeuron !== null && 
          (conn.source_neuron === selectedNeuron.neuron_id || conn.target_neuron === selectedNeuron.neuron_id);
          
        return (
          <ConnectionLine
            key={`conn-${idx}`}
            connection={conn}
            source={source}
            target={target}
            isHighlighted={isHighlighted}
          />
        );
      })}

      <OrbitControls ref={controlsRef} makeDefault />
    </>
  );
};
