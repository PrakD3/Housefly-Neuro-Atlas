import React, { useMemo } from 'react';
import { QuadraticBezierLine } from '@react-three/drei';
import { Neuron, Connection } from '../../api/client';
import * as THREE from 'three';

interface ConnectionLineProps {
  connection: Connection;
  source: Neuron;
  target: Neuron;
  isHighlighted: boolean;
  isDimmed?: boolean;
}

export const ConnectionLine: React.FC<ConnectionLineProps> = ({ source, target, isHighlighted, isDimmed, connection }) => {
  // Use raw coordinates to match the nodes
  const start = useMemo(() => new THREE.Vector3(source.x, source.y, source.z), [source]);
  const end = useMemo(() => new THREE.Vector3(target.x, target.y, target.z), [target]);
  
  // Calculate a deterministic control point for the curve
  const mid = useMemo(() => {
    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    
    // Create a deterministic offset based on neuron IDs and positions
    // This gives an organic "bundle" look where fibers curve outwards
    const dist = start.distanceTo(end);
    
    // Cross product with up vector to find a perpendicular direction
    const direction = new THREE.Vector3().subVectors(end, start).normalize();
    const reference = new THREE.Vector3(0, 1, 0); // Y axis
    
    // If direction is nearly parallel to reference, use X axis
    if (Math.abs(direction.y) > 0.95) {
        reference.set(1, 0, 0);
    }
    
    const perpendicular = new THREE.Vector3().crossVectors(direction, reference).normalize();
    
    // Keep curvature subtle and deterministic
    // Alternate direction of curve based on sum of coordinates
    const sign = (source.x + target.x) > 0 ? 1 : -1;
    const curvature = dist * 0.15 * sign;
    
    midPoint.add(perpendicular.multiplyScalar(curvature));
    
    return midPoint;
  }, [start, end, source, target]);
  
  // Calculate thickness based on weight, but ensure it's visible
  const baseWidth = isHighlighted ? (connection.weight * 1.5) + 2 : connection.weight;
  const lineWidth = isDimmed ? baseWidth * 0.5 : baseWidth;
  
  const color = isHighlighted ? '#38bdf8' : isDimmed ? '#1e293b' : '#475569';
  const opacity = isHighlighted ? 0.9 : isDimmed ? 0.05 : 0.4;
  
  return (
    <QuadraticBezierLine
      start={start}
      end={end}
      mid={mid}
      color={color}
      lineWidth={lineWidth}
      transparent={true}
      opacity={opacity}
      depthWrite={!isDimmed}
    />
  );
};
