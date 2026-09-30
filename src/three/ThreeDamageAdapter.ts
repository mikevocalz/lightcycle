import * as THREE from 'three'
import { DAMAGE_NODES, damageRuntime } from '../runtime/damage.ts'
import type { Player } from '../state/cycleStore.ts'

/**
 * Applies the non-animation half of damage state to one cloned Three.js cycle.
 * Clip playback stays with the host AnimationMixer so wheel/reactor/damage clips
 * can be scheduled without this adapter owning a global timeline.
 */
export function applyThreeDamage(
  root: THREE.Object3D,
  player: Player,
  destroyedProgress = 0,
): ReturnType<typeof damageRuntime> {
  const state = damageRuntime(player, destroyedProgress)
  const detached = new Set(state.detachedNodes)
  for (const name of state.detachedNodes) {
    const node = root.getObjectByName(name)
    if (node) node.visible = state.derezProgress < 0.78
  }
  for (const name of DAMAGE_NODES) {
    if (!detached.has(name)) {
      const node = root.getObjectByName(name)
      if (node) node.visible = true
    }
  }
  return state
}
