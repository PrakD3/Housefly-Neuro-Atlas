import React, { useState } from 'react';
import { Neuron } from '../../api/client';

interface NeuronNodeProps {
  neuron: Neuron;
  isSelected: boolean;
  isDimmed?: boolean;
  scenePosition?: [number, number, number] | null;
  onSelect: (neuron: Neuron) => void;
  onHover: (neuron: Neuron | null) => void;
  simActivity?: number | null;
  simDelta?: number | null;
  simMode?: 'none' | 'perturbed' | 'baseline' | 'delta';
  isTarget?: boolean;
  isModelAffected?: boolean;
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
  simActivity,
  simDelta,
  simMode = 'none',
  isTarget = false,
  isModelAffected = false,
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

  // Base cell type color
  const baseColor = cellTypeColors[neuron.cell_type] ?? "#e2e8f0";

  // Determine color and emissive properties based on simulation mode
  let nodeColor = baseColor;
  let emissiveColor = baseColor;
  let emissiveIntensity = isSelected ? 0.8 : hovered ? 0.5 : 0.2;

  if (isTarget) {
    nodeColor = "#f59e0b"; // vibrant amber target color
    emissiveColor = "#fbbf24";
    emissiveIntensity = 1.0;
  } else if (isModelAffected && simMode === 'none') {
    nodeColor = "#38bdf8"; // bright cyan for model-affected neuron
    emissiveColor = "#38bdf8";
    emissiveIntensity = 0.7;
  } else if (simMode === 'perturbed' || simMode === 'baseline') {
    const act = simActivity !== null && simActivity !== undefined ? simActivity : 0.2;
    // Map normalized model activity [0, 1] to brightness
    emissiveIntensity = 0.1 + act * 0.9;
    if (act > 0.6) {
      nodeColor = "#38bdf8"; // bright cyan glow for high activity
      emissiveColor = "#38bdf8";
    }
  } else if (simMode === 'delta') {
    const delta = simDelta !== null && simDelta !== undefined ? simDelta : 0.0;
    if (delta > 0.02) {
      nodeColor = "#38bdf8"; // cyan for positive model delta
      emissiveColor = "#38bdf8";
      emissiveIntensity = Math.min(1.0, 0.3 + delta * 1.5);
    } else if (delta < -0.02) {
      nodeColor = "#c084fc"; // purple for negative model delta
      emissiveColor = "#a855f7";
      emissiveIntensity = Math.min(1.0, 0.3 + Math.abs(delta) * 1.5);
    } else {
      nodeColor = "#475569";
      emissiveColor = "#1e293b";
      emissiveIntensity = 0.05;
    }
  }

  // Subtle size variation using coordinate hash
  const coordSum = Math.abs(position[0] + position[1] + position[2]);
  const sizeVariation = 0.8 + ((coordSum % 100) / 100) * 0.4;
  const scale = isTarget ? 2.8 : isSelected ? 2.5 : (isModelAffected && !isDimmed) ? 2.2 : hovered ? 2.0 : sizeVariation;

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
        color={isDimmed ? "#334155" : nodeColor}
        emissive={isDimmed ? "#000000" : emissiveColor}
        emissiveIntensity={isDimmed ? 0.05 : emissiveIntensity}
        transparent={true}
        opacity={isDimmed ? 0.1 : 0.9}
        depthWrite={!isDimmed}
      />
    </mesh>
  );
};

