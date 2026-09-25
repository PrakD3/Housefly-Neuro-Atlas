/**
 * VisualizationTransform.ts
 *
 * Coordinate transformation and normalization for 3D visualization.
 *
 * Real neuPrint coordinates are in raw voxel space (e.g. 8 nm / voxel)
 * with values spanning hundreds of thousands of voxels (e.g. 150000, 200000, 80000).
 * Three.js scenes expect coordinates centered around origin within a manageable radius (e.g. [-25, 25]).
 *
 * CRITICAL SCIENTIFIC & ARCHITECTURAL RULES:
 * 1. This transform is strictly a visualization-layer mapping.
 * 2. It NEVER mutates or overrides the anatomical coordinates in the underlying Neuron data model.
 * 3. Neurons without valid coordinates (has_coordinates=false or null x/y/z) return NULL and
 *    MUST NEVER be rendered at (0, 0, 0) or any arbitrary position.
 */

import { Neuron } from "../../api/client";

export interface VisualizationTransform {
  /** Anatomical bounding box center in voxel coordinates [cx, cy, cz] */
  center: [number, number, number];
  /** Scale factor to map voxels into Three.js scene units */
  scale: number;
  /** Target bounding diameter of the scene */
  sceneSize: number;
}

/**
 * Default scene diameter in Three.js units, matching synthetic connectome bounds.
 */
export const DEFAULT_SCENE_DIAMETER = 50;

/**
 * Compute the bounding box and scaling transform for a set of neurons.
 * Ignores neurons without spatial coordinates.
 */
export function computeTransform(
  neurons: Neuron[],
  targetDiameter: number = DEFAULT_SCENE_DIAMETER
): VisualizationTransform {
  const spatialNeurons = neurons.filter(
    (n) => n.has_coordinates && n.x !== null && n.y !== null && n.z !== null
  );

  if (spatialNeurons.length === 0) {
    return {
      center: [0, 0, 0],
      scale: 1,
      sceneSize: targetDiameter,
    };
  }

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;

  for (const n of spatialNeurons) {
    const x = n.x as number;
    const y = n.y as number;
    const z = n.z as number;

    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }

  const spanX = maxX - minX;
  const spanY = maxY - minY;
  const spanZ = maxZ - minZ;
  const maxSpan = Math.max(spanX, spanY, spanZ, 1);

  return {
    center: [(minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2],
    scale: targetDiameter / maxSpan,
    sceneSize: targetDiameter,
  };
}

/**
 * Apply visualization transform to a raw 3D coordinate tuple.
 */
export function applyTransform(
  coord: [number, number, number],
  t: VisualizationTransform
): [number, number, number] {
  return [
    (coord[0] - t.center[0]) * t.scale,
    (coord[1] - t.center[1]) * t.scale,
    (coord[2] - t.center[2]) * t.scale,
  ];
}

/**
 * Convert a Neuron to its 3D scene render position.
 * Returns null if the neuron has no coordinates.
 * NEVER returns [0, 0, 0] as a fallback for missing data.
 */
export function toScenePosition(
  neuron: Neuron,
  transform?: VisualizationTransform | null
): [number, number, number] | null {
  if (
    !neuron.has_coordinates ||
    neuron.x === null ||
    neuron.y === null ||
    neuron.z === null
  ) {
    return null;
  }

  const raw: [number, number, number] = [neuron.x, neuron.y, neuron.z];
  if (!transform) {
    return raw;
  }

  return applyTransform(raw, transform);
}
