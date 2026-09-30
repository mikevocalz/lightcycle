import spec from '../../spec/lightcycle.spec.json' with { type: 'json' }

/**
 * Renderer-independent description of one player's energy identity.
 * Three.js and Viro both consume this; neither one's units leak into it.
 * Intensities are multipliers over the strength authored in the GLB, so the
 * artist keeps control of the relative balance between channels and the
 * runtime only scales it.
 */
export type LightCycleEnergyConfig = {
  energyColor: string
  coreColor: string
  haloColor: string
  energyIntensity: number
  coreIntensity: number
  bloomStrength: number
}

export type CycleColor = keyof typeof spec.colors
export const CYCLE_COLORS = Object.keys(spec.colors) as CycleColor[]

/** Emissive channels, as tagged on the materials in the spec. */
export type EnergyChannel = 'primary' | 'secondary' | 'core' | 'reactor'

/** material name -> channel, for every emissive material in the canonical GLB. */
export const EMISSIVE_CHANNELS: Record<string, EnergyChannel> = Object.fromEntries(
  Object.entries(spec.materials)
    .filter(([, m]) => 'emissive' in m && m.emissive)
    .map(([name, m]) => [name, (m as { channel: EnergyChannel }).channel]),
)

/** Strength authored in the GLB, per material. The runtime multiplies, never replaces. */
export const AUTHORED_STRENGTH: Record<string, number> = Object.fromEntries(
  Object.entries(spec.materials)
    .filter(([, m]) => 'emissionStrength' in m)
    .map(([name, m]) => [name, (m as { emissionStrength: number }).emissionStrength]),
)

export function energyConfig(
  color: CycleColor,
  overrides: Partial<LightCycleEnergyConfig> = {},
): LightCycleEnergyConfig {
  const c = spec.colors[color]
  return {
    energyColor: c.energy,
    coreColor: c.core,
    haloColor: c.halo,
    energyIntensity: 1,
    coreIntensity: 1,
    bloomStrength: 1,
    ...overrides,
  }
}

/**
 * Every emissive channel at zero. This is the §18 quality gate made runnable:
 * apply it and the bike must still read as an expensive machine. If it goes
 * flat, the model is leaning on bloom and the geometry or materials are the
 * thing to fix - not the glow.
 */
export const ENERGY_OFF: LightCycleEnergyConfig = {
  energyColor: '#000000',
  coreColor: '#000000',
  haloColor: '#000000',
  energyIntensity: 0,
  coreIntensity: 0,
  bloomStrength: 0,
}

/** Which config color drives which channel. */
export function channelColor(cfg: LightCycleEnergyConfig, ch: EnergyChannel): string {
  return ch === 'core' ? cfg.coreColor : cfg.energyColor
}

export function channelIntensity(cfg: LightCycleEnergyConfig, ch: EnergyChannel): number {
  return ch === 'core' ? cfg.coreIntensity : cfg.energyIntensity
}
