import type { CycleState } from '../state/cycleStore.ts'

export type ViroSteer = -1 | 0 | 1

export type ViroCompositeClip =
  | 'LC_Viro_Idle'
  | 'LC_Viro_Drive'
  | 'LC_Viro_DriveSteerLeft'
  | 'LC_Viro_DriveSteerRight'
  | 'LC_Viro_Brake'
  | 'LC_Viro_BoostEnter'
  | 'LC_Viro_BoostLoop'
  | 'LC_Viro_BoostExit'
  | 'LC_Viro_HighSpeedEnter'
  | 'LC_Viro_HighSpeedLoop'
  | 'LC_Viro_HighSpeedExit'
  | 'LC_Viro_Damage'
  | 'LC_Viro_DamagedLoop'
  | 'LC_Viro_Crash'
  | 'LC_Viro_Derez'

export type ViroAnimationRequest = {
  name: ViroCompositeClip
  run: true
  loop: boolean
}

/**
 * ViroReact 3.x can switch among named GLB clips, but it documents one active
 * embedded animation at a time (no layered/blended animations yet). The
 * canonical GLB therefore carries composite compatibility clips that combine
 * wheel, reactor, steering/canopy and damage motion for the Viro runtime.
 *
 * Three.js keeps using the original independent clips with AnimationMixer.
 */
export function viroSteadyAnimation(
  cycleState: CycleState,
  steer: ViroSteer = 0,
  highSpeed = false,
): ViroAnimationRequest {
  if (cycleState === 'destroyed') {
    return { name: 'LC_Viro_Derez', run: true, loop: false }
  }
  if (cycleState === 'damaged') {
    return { name: 'LC_Viro_DamagedLoop', run: true, loop: true }
  }
  if (cycleState === 'boost') {
    return {
      name: highSpeed ? 'LC_Viro_HighSpeedLoop' : 'LC_Viro_BoostLoop',
      run: true,
      loop: true,
    }
  }
  if (cycleState === 'driving') {
    if (highSpeed) return { name: 'LC_Viro_HighSpeedLoop', run: true, loop: true }
    if (steer < 0) return { name: 'LC_Viro_DriveSteerLeft', run: true, loop: true }
    if (steer > 0) return { name: 'LC_Viro_DriveSteerRight', run: true, loop: true }
    return { name: 'LC_Viro_Drive', run: true, loop: true }
  }
  return { name: 'LC_Viro_Idle', run: true, loop: true }
}

export type ViroTransition =
  | 'brake'
  | 'boostEnter'
  | 'boostExit'
  | 'highSpeedEnter'
  | 'highSpeedExit'
  | 'damage'
  | 'crash'
  | 'derez'

const TRANSITIONS: Record<ViroTransition, ViroCompositeClip> = {
  brake: 'LC_Viro_Brake',
  boostEnter: 'LC_Viro_BoostEnter',
  boostExit: 'LC_Viro_BoostExit',
  highSpeedEnter: 'LC_Viro_HighSpeedEnter',
  highSpeedExit: 'LC_Viro_HighSpeedExit',
  damage: 'LC_Viro_Damage',
  crash: 'LC_Viro_Crash',
  derez: 'LC_Viro_Derez',
}

/** One-shot clip to play before switching back to viroSteadyAnimation(). */
export function viroTransitionAnimation(kind: ViroTransition): ViroAnimationRequest {
  return { name: TRANSITIONS[kind], run: true, loop: false }
}

/**
 * Hosts should advance transitions through onFinish. There is intentionally no
 * concurrent animation API here: pretending Viro can layer clips would re-open
 * the exact renderer-parity bug this adapter exists to prevent.
 */
export function viroSequence(
  transition: ViroTransition,
  next: ViroAnimationRequest,
): readonly [ViroAnimationRequest, ViroAnimationRequest] {
  return [viroTransitionAnimation(transition), next] as const
}
