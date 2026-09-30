import type { Player } from '../state/cycleStore.ts'

export const DAMAGE_NODES = [
  'LC_Damage_Nose_L',
  'LC_Damage_Nose_R',
  'LC_Damage_Panel_L1',
  'LC_Damage_Panel_L2',
  'LC_Damage_Panel_R1',
  'LC_Damage_Panel_R2',
  'LC_Damage_Rear_L',
  'LC_Damage_Rear_R',
  'LC_Damage_ReactorCover',
] as const

export type DamageNode = (typeof DAMAGE_NODES)[number]

export type DamageRuntime = {
  severity: number
  clip: 'LC_Damage' | 'LC_Derez' | null
  detachedNodes: DamageNode[]
  energyMultiplier: number
  sparkOrigins: ('LC_FX_Impact_L' | 'LC_FX_Impact_R')[]
  derezProgress: number
}

/**
 * Deterministic gameplay-to-visual mapping. It never mutates the GLB; renderers
 * play the named clip and toggle detachable nodes on the player's cloned scene.
 */
export function damageRuntime(player: Player, destroyedProgress = 0): DamageRuntime {
  const severity = Math.max(0, Math.min(1, 1 - player.health))
  const destroyed = player.isDestroyed || player.cycleState === 'destroyed'
  const detachCount = destroyed
    ? DAMAGE_NODES.length
    : Math.min(DAMAGE_NODES.length, Math.floor(severity * (DAMAGE_NODES.length + 1)))

  const sparkOrigins: DamageRuntime['sparkOrigins'] = []
  if (severity >= 0.25) sparkOrigins.push('LC_FX_Impact_L')
  if (severity >= 0.55) sparkOrigins.push('LC_FX_Impact_R')

  return {
    severity,
    clip: destroyed ? 'LC_Derez' : severity > 0 ? 'LC_Damage' : null,
    detachedNodes: DAMAGE_NODES.slice(0, detachCount),
    energyMultiplier: destroyed ? 0 : Math.max(0.28, 1 - severity * 0.72),
    sparkOrigins,
    derezProgress: destroyed ? Math.max(0, Math.min(1, destroyedProgress)) : 0,
  }
}
