import type { Player } from '../state/cycleStore.ts'
import { energyConfig } from '../energy/config.ts'

/**
 * Rive Data Binding view-model contract. Keep these property names stable in
 * the .riv HUD/leaderboard so web and React Native can share the same artboard.
 */
export type LightCycleHudModel = {
  playerName: string
  playerColor: string
  coreColor: string
  haloColor: string
  speed: number
  boost: number
  health: number
  score: number
  damaged: boolean
  destroyed: boolean
}

export interface RiveViewModelWriter {
  setString(name: string, value: string): void
  setNumber(name: string, value: number): void
  setBoolean(name: string, value: boolean): void
  setColor(name: string, value: string): void
}

export function lightCycleHudModel(player: Player, score = 0): LightCycleHudModel {
  const cfg = energyConfig(player.cycleColor)
  return {
    playerName: player.playerName,
    playerColor: cfg.energyColor,
    coreColor: cfg.coreColor,
    haloColor: cfg.haloColor,
    speed: player.speed,
    boost: player.boost,
    health: player.health,
    score,
    damaged: player.cycleState === 'damaged',
    destroyed: player.isDestroyed || player.cycleState === 'destroyed',
  }
}

export function bindLightCycleHud(writer: RiveViewModelWriter, model: LightCycleHudModel): void {
  writer.setString('playerName', model.playerName)
  writer.setColor('playerColor', model.playerColor)
  writer.setColor('coreColor', model.coreColor)
  writer.setColor('haloColor', model.haloColor)
  writer.setNumber('speed', model.speed)
  writer.setNumber('boost', model.boost)
  writer.setNumber('health', model.health)
  writer.setNumber('score', model.score)
  writer.setBoolean('damaged', model.damaged)
  writer.setBoolean('destroyed', model.destroyed)
}
