import { EMISSIVE_CHANNELS, channelColor, channelIntensity, type LightCycleEnergyConfig } from '../energy/config.ts'

/**
 * Binds a LightCycleEnergyConfig onto one player's bike in ViroReact.
 *
 * This cannot be a thin mirror of the Three.js adapter, for three reasons
 * established against ViroReact 3.0.1 and the virocore fork:
 *
 * 1. ViroMaterial has NO emissive property. Not emissiveColor, not
 *    emissiveIntensity, not emissiveTexture. The native engine has a full
 *    emissive pipeline, but it is populated only by the glTF importer reading
 *    the file's own emissiveFactor - there is no JS setter, and a `surface`
 *    shader modifier cannot reach it either. So energy is expressed as an
 *    unlit additive surface: lightingModel 'Constant' + blendMode 'Add', with
 *    bloomThreshold gating whether it feeds the native bloom pass.
 *
 * 2. Viro cannot address a named sub-node from JS. Viro3DObject exposes only
 *    getBoundingBoxAsync and getMorphTargets; `materials` and `shaderOverrides`
 *    are whole-model operations. LC_Reactor_Ring_A cannot be targeted at
 *    runtime. Material NAME is the only handle, which is why the canonical GLB
 *    gives every independently-controlled region its own material slot.
 *
 * 3. ViroMaterials is a single global name-keyed registry. Registering
 *    MAT_LC_EMISSIVE_PRIMARY twice mutates the shared native material for every
 *    node referencing it, so two players sharing a material name share a colour.
 *    Every player therefore mints its own uniquely-suffixed names.
 *
 * bloomStrength has no Viro equivalent: bloomEnabled is a binary scene-navigator
 * toggle and bloomThreshold is a per-material luminance gate, not an intensity.
 * It is approximated by driving diffuseColor overbright against a fixed
 * threshold. Visual equivalence is the goal, not matching numbers.
 */

export type ViroMaterialDef = {
  lightingModel: 'Constant' | 'Lambert' | 'Blinn' | 'Phong' | 'PBR'
  diffuseColor: string
  blendMode?: 'None' | 'Alpha' | 'Add' | 'Subtract' | 'Multiply' | 'Screen'
  bloomThreshold?: number
  writesToDepthBuffer?: boolean
  readsFromDepthBuffer?: boolean
}

/** Minimal surface of the real ViroMaterials module, so this file stays testable. */
export type ViroMaterialsModule = {
  createMaterials: (defs: Record<string, ViroMaterialDef>) => void
}

/** Below this, Viro's native bloom pass ignores the surface entirely. */
const BLOOM_GATE = 0.6

function overbright(hex: string, gain: number): string {
  // Viro takes CSS colour strings, so HDR has to be faked by scaling toward
  // white: past 1.0 the channel clips, and clipping toward white is what reads
  // as "hotter" once the bloom pass picks it up.
  const n = parseInt(hex.slice(1), 16)
  const scale = (c: number) => Math.round(Math.min(255, c * Math.min(gain, 1) + 255 * Math.max(0, gain - 1) * 0.6))
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255]
  return `#${[scale(r), scale(g), scale(b)].map((c) => c.toString(16).padStart(2, '0')).join('')}`
}

export class ViroLightCycleMaterialAdapter {
  /** Suffix that keeps this player's materials out of every other player's. */
  readonly ns: string
  private readonly viroMaterials: ViroMaterialsModule

  constructor(playerId: string, viroMaterials: ViroMaterialsModule) {
    // The registry is global and name-keyed, so the namespace is the isolation.
    this.ns = `__p_${playerId.replace(/[^A-Za-z0-9_]/g, '')}`
    this.viroMaterials = viroMaterials
  }

  /** Material names to hand to the Viro3DObject `materials` / `shaderOverrides` prop. */
  materialNames(): string[] {
    return Object.keys(EMISSIVE_CHANNELS).map((n) => `${n}${this.ns}`)
  }

  private defs(cfg: LightCycleEnergyConfig): Record<string, ViroMaterialDef> {
    const out: Record<string, ViroMaterialDef> = {}
    for (const [name, ch] of Object.entries(EMISSIVE_CHANNELS)) {
      const intensity = channelIntensity(cfg, ch)
      out[`${name}${this.ns}`] = {
        lightingModel: 'Constant', // unlit: the energy must not take scene lighting
        diffuseColor: overbright(channelColor(cfg, ch), intensity * (cfg.bloomStrength || 1)),
        blendMode: 'Add',
        // Zero intensity must drop out of the bloom pass entirely, or a "dark"
        // bike still glows faintly - which would defeat the lights-off gate.
        bloomThreshold: intensity <= 0 ? 1.0 : BLOOM_GATE,
        writesToDepthBuffer: false,
      }
    }
    return out
  }

  apply(cfg: LightCycleEnergyConfig): void {
    this.viroMaterials.createMaterials(this.defs(cfg))
  }

  /** The doc 18 gate. Additive black composites to nothing, so the energy vanishes. */
  lightsOff(): void {
    const off: Record<string, ViroMaterialDef> = {}
    for (const name of Object.keys(EMISSIVE_CHANNELS)) {
      off[`${name}${this.ns}`] = {
        lightingModel: 'Constant',
        diffuseColor: '#000000',
        blendMode: 'Add',
        bloomThreshold: 1.0,
        writesToDepthBuffer: false,
      }
    }
    this.viroMaterials.createMaterials(off)
  }
}

/**
 * Parity gaps, so nobody rediscovers them on device.
 *
 * Absent from ViroMaterial with no workaround short of a full custom shader:
 * clearcoat, anisotropy, transmission and ior. The black clearcoat composite and
 * the brushed-metal anisotropy that carry the lights-off look on the web will
 * render as plain roughness in XR. Budget for the XR build looking flatter, and
 * lean harder on normal maps and AO there.
 *
 * Also requires on-device verification before being relied on:
 *  - whether one Viro3DObject can run several named clips at once on different
 *    sub-nodes. ViroAnimation is a singular config and the type shape suggests
 *    one active clip per instance, which would break independent wheel and
 *    reactor motion. UNVERIFIED.
 *  - whether shaderOverrides on separate Viro3DObject instances genuinely
 *    isolates per-player material state, or whether the global registry leaks
 *    across instances anyway. UNVERIFIED, and the whole multiplayer colour story
 *    on XR rests on it.
 *  - PICO. It appears nowhere in the ReactVision platform matrix; only Meta
 *    Quest (OpenXR) is a named target.
 */
export const VIRO_PARITY_GAPS = [
  'no emissive channel; energy is Constant + Add diffuse',
  'no per-node addressing; material name is the only handle',
  'global material registry; per-player namespacing is mandatory',
  'bloomStrength approximated via overbright diffuse against a fixed threshold',
  'clearcoat, anisotropy, transmission, ior all absent',
] as const
