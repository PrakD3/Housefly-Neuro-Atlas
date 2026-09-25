import React, { useState } from 'react';
import { Neuron } from '../../api/client';

interface NeuronNodeProps {
  neuron: Neuron;
  isSelected: boolean;
  isDimmed?: boolean;
  scenePosition?: [number, number, number] | null;
  onSelect: (neuron: Neuron) => void;
  onHover: (neuron: Neuron | null) => void;
}

const cellTypeColors: Record<string, string> = {
  "Sensory":     "#fbbf24",
  "Interneuron": "#a78bfa",
  "Projection":  "#f87171",
  "Motor":       "#34d399",
  "Modulatory":  "#38bdf8",
  // Real connectome superClass values
  "descending":  "#f97316",
  "ascending":   "#a3e635",
  "visual":      "#22d3ee",
  "central":     "#c084fc",
  "sensory":     "#fbbf24",
  "motor":       "#34d399",
};

export const NeuronNode: React.FC<NeuronNodeProps> = ({
  neuron,
  isSelected,
  isDimmed,
  scenePosition,
  onSelect,
  onHover,
}) => {
  const [hovered, setHovered] = useState(false);

  /**
   * Gate: neurons without coordinates must NEVER be rendered in 3D space.
   * If scenePosition is explicitly null, or if coordinates are absent, do not render.
   */
  if (scenePosition === null) {
    return null;
  }

  if (scenePosition === undefined && (!neuron.has_coordinates || neuron.x === null || neuron.y === null || neuron.z === null)) {
    return null;
  }

  const position: [number, number, number] = scenePosition !== undefined
    ? scenePosition
    : [neuron.x as number, neuron.y as number, neuron.z as number];

  const color = cellTypeColors[neuron.cell_type] ?? "#e2e8f0";

  // Subtle size variation using coordinate hash
  const coordSum = Math.abs(position[0] + position[1] + position[2]);
  const sizeVariation = 0.8 + ((coordSum % 100) / 100) * 0.4;
  const scale = isSelected ? 2.5 : hovered ? 2.0 : sizeVariation;


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
