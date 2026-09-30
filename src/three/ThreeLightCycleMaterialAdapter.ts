import * as THREE from 'three'
import {
  AUTHORED_STRENGTH,
  EMISSIVE_CHANNELS,
  ENERGY_OFF,
  channelColor,
  channelIntensity,
  type EnergyChannel,
  type LightCycleEnergyConfig,
} from '../energy/config.ts'

/**
 * Binds a LightCycleEnergyConfig onto one player's instance of the canonical GLB.
 *
 * Instance safety is the whole point. `scene.clone()` shares materials by
 * reference, so recoloring a clone would recolor every player. This clones
 * exactly the emissive materials - the ~4 the spec tags - and leaves the
 * graphite, metal, rubber, carbon and glass shared across all players.
 * `Material.clone()` copies scalars and colors but keeps texture pointers, so
 * no map is re-uploaded to the GPU, and MeshStandardMaterial is a fixed uber
 * shader, so changing `.emissive` costs no recompile.
 *
 * Verified against three 0.186.1.
 */
export class ThreeLightCycleMaterialAdapter {
  readonly root: THREE.Object3D
  /** materialName -> this player's private clone, with the channel it answers to */
  private readonly owned = new Map<
    string,
    { mat: THREE.MeshStandardMaterial; ch: EnergyChannel; authored: number }
  >()
  private config: LightCycleEnergyConfig | null = null

  /**
   * @param source the scene returned by GLTFLoader. Never mutated.
   */
  constructor(source: THREE.Object3D) {
    this.root = source.clone(true)
    this.claimEmissiveMaterials()
  }

  /** Swap every emissive material for a private clone, once per material name. */
  private claimEmissiveMaterials(): void {
    this.root.traverse((o) => {
      const mesh = o as THREE.Mesh
      if (!mesh.isMesh) return
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
      const swapped = mats.map((m) => {
        const ch = EMISSIVE_CHANNELS[m.name]
        if (!ch) return m // shared across all players, deliberately
        let mine = this.owned.get(m.name)
        if (!mine) {
          const clone = (m as THREE.MeshStandardMaterial).clone()
          // GLTFLoader writes KHR_materials_emissive_strength straight into
          // emissiveIntensity, so the authored value is already here. Capture it
          // before the first apply, or repeated applies would compound.
          const authored =
            (m as THREE.MeshStandardMaterial).emissiveIntensity ?? AUTHORED_STRENGTH[m.name] ?? 1
          mine = { mat: clone, ch, authored }
          this.owned.set(m.name, mine)
        }
        return mine.mat
      })
      const first = swapped[0]
      if (first) mesh.material = Array.isArray(mesh.material) ? swapped : first
    })
  }

  apply(cfg: LightCycleEnergyConfig): void {
    this.config = cfg
    for (const { mat, ch, authored } of this.owned.values()) {
      mat.emissive.set(channelColor(cfg, ch)).convertSRGBToLinear()
      mat.emissiveIntensity = authored * channelIntensity(cfg, ch)
    }
  }

  /** The §18 gate: kill every emissive and judge the machine on its materials alone. */
  lightsOff(): void {
    this.apply(ENERGY_OFF)
  }

  /** Bloom is a scene-wide pass, so the player's strength is read, not pushed. */
  get bloomStrength(): number {
    return this.config?.bloomStrength ?? 0
  }

  /** Only the clones are ours to free; shared materials outlive this instance. */
  dispose(): void {
    for (const { mat } of this.owned.values()) mat.dispose()
    this.owned.clear()
  }
}

/**
 * Renderer settings the six colors depend on.
 *
 * NeutralToneMapping (Khronos PBR Neutral) rolls off luminance while holding
 * hue. ACESFilmic pushes hot saturated values toward white, which is exactly
 * the §17 failure mode the QA matrix screens for - gold flattening to yellow,
 * red drifting orange, white clipping to a featureless blob.
 */
export function configureRenderer(renderer: THREE.WebGLRenderer): void {
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.NeutralToneMapping
  renderer.toneMappingExposure = 0.9
}

/**
 * One bloom pass serves every player. Threshold sits above the brightest the
 * neutral body materials reach, so only emissive-boosted pixels bloom and each
 * keeps its own hue - no per-player pass, no layer mask.
 */
export const BLOOM_DEFAULTS = { strength: 1.2, radius: 0.4, threshold: 0.9 } as const
