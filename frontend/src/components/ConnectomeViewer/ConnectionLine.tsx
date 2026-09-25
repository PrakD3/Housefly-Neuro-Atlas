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
  sceneSourcePos?: [number, number, number] | null;
  sceneTargetPos?: [number, number, number] | null;
}

export const ConnectionLine: React.FC<ConnectionLineProps> = ({
  source,
  target,
  isHighlighted,
  isDimmed,
  connection,
  sceneSourcePos,
  sceneTargetPos,
}) => {
  /**
   * Gate: both endpoints must have coordinates to draw a line.
   * If either neuron has has_coordinates=false (or null position), the line cannot be drawn.
   * Never substitute (0,0,0) for missing coordinates.
   */
  if (sceneSourcePos === null || sceneTargetPos === null) {
    return null;
  }

  if (sceneSourcePos === undefined && (!source.has_coordinates || source.x === null || source.y === null || source.z === null)) {
    return null;
  }

  if (sceneTargetPos === undefined && (!target.has_coordinates || target.x === null || target.y === null || target.z === null)) {
    return null;
  }

  const start = useMemo(
    () => sceneSourcePos
      ? new THREE.Vector3(...sceneSourcePos)
      : new THREE.Vector3(source.x!, source.y!, source.z!),
    [source, sceneSourcePos]
  );
  const end = useMemo(
    () => sceneTargetPos
      ? new THREE.Vector3(...sceneTargetPos)
      : new THREE.Vector3(target.x!, target.y!, target.z!),
    [target, sceneTargetPos]
  );


  const mid = useMemo(() => {
    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    const dist = start.distanceTo(end);
    const direction = new THREE.Vector3().subVectors(end, start).normalize();
    const reference = new THREE.Vector3(0, 1, 0);
    if (Math.abs(direction.y) > 0.95) reference.set(1, 0, 0);
    const perpendicular = new THREE.Vector3()
      .crossVectors(direction, reference)
      .normalize();
    const sign = (source.x! + target.x!) > 0 ? 1 : -1;
    const curvature = dist * 0.15 * sign;
    midPoint.add(perpendicular.multiplyScalar(curvature));
    return midPoint;
  }, [start, end, source, target]);

  const baseWidth = isHighlighted ? connection.weight * 1.5 + 2 : connection.weight;
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
