import React, { useState } from 'react';
import { Neuron } from '../../api/client';

interface NeuronNodeProps {
  neuron: Neuron;
  isSelected: boolean;
  onSelect: (neuron: Neuron) => void;
  onHover: (neuron: Neuron | null) => void;
}

// Map cell types to colors
const cellTypeColors: Record<string, string> = {
  "Kenyon_Cell": "#3b82f6", // blue
  "Projection_Neuron": "#ef4444", // red
  "Motor_Neuron": "#10b981", // green
  "Sensory_Neuron": "#f59e0b", // yellow
  "Interneuron": "#8b5cf6", // purple
};

export const NeuronNode: React.FC<NeuronNodeProps> = ({ neuron, isSelected, onSelect, onHover }) => {
  const [hovered, setHovered] = useState(false);
  const color = cellTypeColors[neuron.cell_type] || "#ffffff";
  const scale = isSelected ? 3 : hovered ? 2 : 1;

  // We scale down the synthetic coordinates slightly to fit better in standard camera view
  // and shift by -5 so the cluster is centered at the origin
  const position: [number, number, number] = [
    (neuron.x / 10) - 5,
    (neuron.y / 10) - 5,
    (neuron.z / 10) - 5
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
      <sphereGeometry args={[0.5, 16, 16]} />
      <meshStandardMaterial color={color} emissive={isSelected ? color : "#000000"} emissiveIntensity={isSelected ? 0.5 : 0} />
    </mesh>
  );
};
