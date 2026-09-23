import React, { useState } from 'react';
import { Neuron } from '../../api/client';

interface NeuronNodeProps {
  neuron: Neuron;
  isSelected: boolean;
  isDimmed?: boolean;
  onSelect: (neuron: Neuron) => void;
  onHover: (neuron: Neuron | null) => void;
}

// Map cell types to colors (restrained palette with accents)
const cellTypeColors: Record<string, string> = {
  "Sensory": "#fbbf24",     // yellow
  "Interneuron": "#a78bfa", // purple
  "Projection": "#f87171",  // red
  "Motor": "#34d399",       // green
  "Modulatory": "#38bdf8",  // cyan
};

export const NeuronNode: React.FC<NeuronNodeProps> = ({ neuron, isSelected, isDimmed, onSelect, onHover }) => {
  const [hovered, setHovered] = useState(false);
  const color = cellTypeColors[neuron.cell_type] || "#e2e8f0";
  
  // Size variation based on degree could be nice, but for now we just use a subtle random/hash size
  // Let's use the sum of x+y+z to generate a consistent subtle variation [0.8 to 1.2]
  const sizeVariation = 0.8 + ((Math.abs(neuron.x + neuron.y + neuron.z) % 100) / 100) * 0.4;
  
  const scale = isSelected ? 2.5 : hovered ? 2.0 : sizeVariation;
  
  // Position
  const position: [number, number, number] = [
    neuron.x,
    neuron.y,
    neuron.z
  ];

  return (
    <mesh
      position={position}
      scale={scale}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(neuron);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        onHover(neuron);
      }}
      onPointerOut={() => {
        setHovered(false);
        onHover(null);
      }}
    >
      <sphereGeometry args={[0.5, 32, 32]} />
      <meshStandardMaterial 
        color={isDimmed ? "#334155" : color} 
        emissive={isDimmed ? "#000000" : color} 
        emissiveIntensity={isSelected ? 0.8 : hovered ? 0.5 : 0.2} 
        transparent={true}
        opacity={isDimmed ? 0.1 : 0.9}
        depthWrite={!isDimmed}
      />
    </mesh>
  );
};
