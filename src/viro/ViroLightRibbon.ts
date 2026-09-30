import type { LightCycleEnergyConfig } from '../energy/config.ts'
import type { LightRibbonPath, TrailPoint } from '../runtime/trail.ts'

export type ViroRibbonWall = {
  key: string
  position: [number, number, number]
  rotation: [number, number, number]
  vertices: [[number, number], [number, number], [number, number], [number, number]]
}

export type ViroRibbonDescriptor = {
  materialName: string
  coreMaterialName: string
  walls: ViroRibbonWall[]
  corePoints: [number, number, number][]
}

/**
 * Converts the shared Y-up trail into props for ViroPolygon + ViroPolyline.
 *
 * Render each wall with:
 *   <ViroPolygon position={wall.position} rotation={wall.rotation}
 *                vertices={wall.vertices} materials={descriptor.materialName} />
 * and the hot edge with one ViroPolyline per contiguous segment.
 *
 * Viro's documented Polygon and Polyline primitives keep the trail runtime
 * geometry instead of baking it into the cycle GLB.
 */
export function toViroLightRibbon(
  path: LightRibbonPath,
  playerMaterialNamespace: string,
  height = 1.05,
): ViroRibbonDescriptor[] {
  return path.segments().map((segment, si) => {
    const walls: ViroRibbonWall[] = []
    const corePoints: [number, number, number][] = segment.map((p) => [
      p.x, p.y + height, p.z,
    ])

    for (let i = 1; i < segment.length; i++) {
      const a = segment[i - 1]!
      const b = segment[i]!
      const dx = b.x - a.x
      const dz = b.z - a.z
      const length = Math.hypot(dx, dz)
      if (length <= 1e-6) continue
      // A local ViroPolygon lies in XY. Rotate its local X onto the horizontal
      // XZ trail direction while local Y remains world-up.
      const yawDeg = -Math.atan2(dz, dx) * 180 / Math.PI
      walls.push({
        key: `trail-${si}-${i - 1}`,
        position: [(a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2],
        rotation: [0, yawDeg, 0],
        vertices: [
          [-length / 2, 0],
          [length / 2, 0],
          [length / 2, height],
          [-length / 2, height],
        ],
      })
    }

    return {
      materialName: `MAT_LC_TRAIL_${playerMaterialNamespace}_energy`,
      coreMaterialName: `MAT_LC_TRAIL_${playerMaterialNamespace}_core`,
      walls,
      corePoints,
    }
  })
}

export type ViroTrailMaterialDef = {
  lightingModel: 'Constant'
  diffuseColor: string
  blendMode: 'Add'
  bloomThreshold: number
  writesToDepthBuffer: false
}

/** Material definitions can be fed to ViroMaterials.createMaterials(). */
export function viroLightRibbonMaterials(
  cfg: LightCycleEnergyConfig,
  playerMaterialNamespace: string,
): Record<string, ViroTrailMaterialDef> {
  return {
    [`MAT_LC_TRAIL_${playerMaterialNamespace}_energy`]: {
      lightingModel: 'Constant',
      diffuseColor: cfg.energyColor,
      blendMode: 'Add',
      bloomThreshold: cfg.energyIntensity > 0 ? 0.55 : 1,
      writesToDepthBuffer: false,
    },
    [`MAT_LC_TRAIL_${playerMaterialNamespace}_core`]: {
      lightingModel: 'Constant',
      diffuseColor: cfg.coreColor,
      blendMode: 'Add',
      bloomThreshold: cfg.coreIntensity > 0 ? 0.72 : 1,
      writesToDepthBuffer: false,
    },
  }
}
