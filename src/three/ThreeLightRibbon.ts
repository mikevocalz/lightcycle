import * as THREE from 'three'
import type { LightCycleEnergyConfig } from '../energy/config.ts'
import { LightRibbonPath } from '../runtime/trail.ts'

export type ThreeLightRibbonOptions = {
  height?: number
  opacity?: number
}

/**
 * Runtime-generated TRON wall. The saturated wall and white-hot top edge are
 * separate materials so bloom can keep a hot core without washing player hue.
 */
export class ThreeLightRibbon {
  readonly root = new THREE.Group()
  readonly path: LightRibbonPath
  readonly wallMaterial: THREE.MeshBasicMaterial
  readonly coreMaterial: THREE.LineBasicMaterial
  readonly height: number

  private wall = new THREE.Mesh(new THREE.BufferGeometry())
  private core = new THREE.LineSegments(new THREE.BufferGeometry())

  constructor(path = new LightRibbonPath(), options: ThreeLightRibbonOptions = {}) {
    this.path = path
    this.height = options.height ?? 1.05
    this.wallMaterial = new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: options.opacity ?? 0.88,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
      toneMapped: false,
    })
    this.coreMaterial = new THREE.LineBasicMaterial({
      transparent: true,
      opacity: 1,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
    })
    this.wall.material = this.wallMaterial
    this.core.material = this.coreMaterial
    this.wall.frustumCulled = false
    this.core.frustumCulled = false
    this.root.add(this.wall, this.core)
  }

  applyEnergy(cfg: LightCycleEnergyConfig): void {
    this.wallMaterial.color.set(cfg.energyColor).multiplyScalar(Math.max(0, cfg.energyIntensity))
    this.coreMaterial.color.set(cfg.coreColor).multiplyScalar(Math.max(0, cfg.coreIntensity))
    this.root.visible = cfg.energyIntensity > 0 || cfg.coreIntensity > 0
  }

  rebuild(): void {
    const wallPositions: number[] = []
    const wallIndices: number[] = []
    const corePositions: number[] = []

    for (const segment of this.path.segments()) {
      for (let i = 1; i < segment.length; i++) {
        const a = segment[i - 1]!
        const b = segment[i]!
        const base = wallPositions.length / 3
        wallPositions.push(
          a.x, a.y, a.z,
          a.x, a.y + this.height, a.z,
          b.x, b.y, b.z,
          b.x, b.y + this.height, b.z,
        )
        wallIndices.push(base, base + 2, base + 1, base + 1, base + 2, base + 3)
        corePositions.push(
          a.x, a.y + this.height, a.z,
          b.x, b.y + this.height, b.z,
        )
      }
    }

    const wallGeometry = new THREE.BufferGeometry()
    wallGeometry.setAttribute('position', new THREE.Float32BufferAttribute(wallPositions, 3))
    wallGeometry.setIndex(wallIndices)
    wallGeometry.computeVertexNormals()

    const coreGeometry = new THREE.BufferGeometry()
    coreGeometry.setAttribute('position', new THREE.Float32BufferAttribute(corePositions, 3))

    this.wall.geometry.dispose()
    this.core.geometry.dispose()
    this.wall.geometry = wallGeometry
    this.core.geometry = coreGeometry
  }

  dispose(): void {
    this.wall.geometry.dispose()
    this.core.geometry.dispose()
    this.wallMaterial.dispose()
    this.coreMaterial.dispose()
    this.root.clear()
  }
}
