import React, { useMemo, useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
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
  center: [number, number, number];
  width: number;
  height: number;
  depth: number;
}

export const Scene: React.FC<SceneProps> = ({ 
  neurons, 
  connections, 
  neighborsData, 
  selectedNeuron, 
  showConnections,
  onSelectNeuron, 
  onHoverNeuron,
  center,
  width,
  height,
  depth
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

  // Initial and reframing camera setup
  useEffect(() => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      const camera = controls.object as THREE.PerspectiveCamera;
      // Calculate distance based on both vertical and horizontal FOV
      const vFovRad = (camera.fov * Math.PI) / 180;
      
      // Calculate required distances
      // The dimensions of the neural system we want to fit
      // Adding a small padding to depth since objects have volume
      const totalDepth = depth + 10;
      
      const requiredVDistance = (height / 2) / Math.tan(vFovRad / 2);
      
      // Horizontal FOV calculation based on aspect ratio
      const hFovRad = 2 * Math.atan(Math.tan(vFovRad / 2) * camera.aspect);
      const requiredHDistance = (width / 2) / Math.tan(hFovRad / 2);
      
      // Use whichever requires the greater distance, plus a 1.25x safety margin
      // so it occupies ~60-75% of the viewport (if we multiply distance by ~1.33)
      let distance = Math.max(requiredVDistance, requiredHDistance) * 1.5;
      
      // Add half depth so front neurons don't get too close
      distance += (totalDepth / 2);
      
      // Minimum distance to prevent clipping
      if (distance < 10) distance = 10;
      
      // Only set position if no neuron is selected (global framing)
      if (!selectedNeuron) {
        camera.position.set(center[0], center[1], center[2] + distance);
        controls.target.set(center[0], center[1], center[2]);
        controls.update();
      }
    }
  }, [center, width, height, depth, selectedNeuron]);

  // Smooth camera targeting on selection.
  // Only move toward the neuron if it actually has spatial coordinates.
  useFrame(() => {
    if (
      selectedNeuron &&
      selectedNeuron.has_coordinates &&
      selectedNeuron.x !== null &&
      selectedNeuron.y !== null &&
      selectedNeuron.z !== null &&
      controlsRef.current
    ) {
      const targetPos = new THREE.Vector3(
        selectedNeuron.x,
        selectedNeuron.y,
        selectedNeuron.z
      );
      controlsRef.current.target.lerp(targetPos, 0.05);
      controlsRef.current.update();
    }
  });

  return (
    <>
      <color attach="background" args={['#0b0f19']} />
      <ambientLight intensity={0.6} />
      <pointLight position={[20, 20, 20]} intensity={1.5} />
      <pointLight position={[-20, -20, -20]} intensity={0.5} />
      
      {/* Neurons */}
      {neurons.map(neuron => {
        const isSelected = selectedNeuron?.neuron_id === neuron.neuron_id || highlightedNeuronIds.has(neuron.neuron_id);
        const isDimmed = selectedNeuron !== null && !isSelected;
        
        return (
          <NeuronNode
            key={neuron.neuron_id}
            neuron={neuron}
            isSelected={isSelected}
            isDimmed={isDimmed}
            onSelect={onSelectNeuron}
            onHover={onHoverNeuron}
          />
        );
      })}
      
      {/* Connections */}
      {showConnections && connections.map((conn, idx) => {
        const source = neuronMap.get(conn.source_neuron);
        const target = neuronMap.get(conn.target_neuron);
        
        if (!source || !target) return null;
        
        const isHighlighted = selectedNeuron !== null && 
          (conn.source_neuron === selectedNeuron.neuron_id || conn.target_neuron === selectedNeuron.neuron_id);
        const isDimmed = selectedNeuron !== null && !isHighlighted;
          
        return (
          <ConnectionLine
            key={`conn-${idx}`}
            connection={conn}
            source={source}
            target={target}
            isHighlighted={isHighlighted}
            isDimmed={isDimmed}
          />
        );
      })}

      <OrbitControls ref={controlsRef} makeDefault dampingFactor={0.05} />
    </>
  );
};
