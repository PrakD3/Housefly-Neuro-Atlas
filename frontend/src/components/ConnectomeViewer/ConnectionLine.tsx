import React from 'react';
import { Line } from '@react-three/drei';
import { Neuron, Connection } from '../../api/client';

interface ConnectionLineProps {
  connection: Connection;
  source: Neuron;
  target: Neuron;
  isHighlighted: boolean;
}

export const ConnectionLine: React.FC<ConnectionLineProps> = ({ source, target, isHighlighted, connection }) => {
  // Scale down the coordinates to match the nodes and shift to center
  const start: [number, number, number] = [(source.x / 10) - 5, (source.y / 10) - 5, (source.z / 10) - 5];
  const end: [number, number, number] = [(target.x / 10) - 5, (target.y / 10) - 5, (target.z / 10) - 5];
  
  // Calculate thickness based on weight, but ensure it's visible
  const lineWidth = isHighlighted ? (connection.weight * 2) + 2 : connection.weight;
  const color = isHighlighted ? '#ffffff' : '#4b5563'; // White if highlighted, gray otherwise
  
  return (
    <Line
      points={[start, end]}
      color={color}
      lineWidth={lineWidth}
      transparent={true}
      opacity={isHighlighted ? 0.8 : 0.3}
    />
  );
};
