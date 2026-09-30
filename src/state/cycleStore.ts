import { create } from 'zustand'
import { energyConfig, type CycleColor, type LightCycleEnergyConfig } from '../energy/config.ts'

export type CycleState = 'idle' | 'driving' | 'boost' | 'damaged' | 'destroyed'

export type Player = {
  playerId: string
  playerName: string
  cycleColor: CycleColor
  cycleState: CycleState
  speed: number
  boost: number
  health: number
  isDestroyed: boolean
}

type Store = {
  players: Record<string, Player>
  localPlayerId: string | null
  join: (p: Pick<Player, 'playerId' | 'playerName' | 'cycleColor'> & { local?: boolean }) => void
  leave: (playerId: string) => void
  setColor: (playerId: string, cycleColor: CycleColor) => void
  update: (playerId: string, patch: Partial<Omit<Player, 'playerId'>>) => void
}

/**
 * Single source of truth for cycle identity and state. No React useState for any
 * of this - a player's color has to reach the bike materials, trail, FX, HUD and
 * leaderboard, and component-local state cannot serve all of them.
 *
 * Players are keyed by id rather than held as a single "current player" so two
 * bikes with different colors can render at once, which is the multiplayer
 * requirement the whole material architecture exists to support.
 */
export const useCycleStore = create<Store>((set) => ({
  players: {},
  localPlayerId: null,

  join: ({ playerId, playerName, cycleColor, local }) =>
    set((s) => ({
      localPlayerId: local ? playerId : s.localPlayerId,
      players: {
        ...s.players,
        [playerId]: {
          playerId,
          playerName,
          cycleColor,
          cycleState: 'idle',
          speed: 0,
          boost: 0,
          health: 1,
          isDestroyed: false,
        },
      },
    })),

  leave: (playerId) =>
    set((s) => {
      const { [playerId]: _gone, ...rest } = s.players
      return { players: rest, localPlayerId: s.localPlayerId === playerId ? null : s.localPlayerId }
    }),

  setColor: (playerId, cycleColor) =>
    set((s) =>
      s.players[playerId]
        ? { players: { ...s.players, [playerId]: { ...s.players[playerId], cycleColor } } }
        : s,
    ),

  update: (playerId, patch) =>
    set((s) =>
      s.players[playerId]
        ? { players: { ...s.players, [playerId]: { ...s.players[playerId], ...patch } } }
        : s,
    ),
}))

/** Subscribe to one player's energy config. Changing cycleColor re-runs this and nothing else. */
export function usePlayerEnergy(playerId: string): LightCycleEnergyConfig | null {
  return useCycleStore((s) => {
    const p = s.players[playerId]
    if (!p) return null
    // Damage and boost ride on top of the player's identity colour.
    if (p.cycleState === 'boost') return energyConfig(p.cycleColor, { energyIntensity: 1.6, coreIntensity: 2.2, bloomStrength: 1.5 })
    if (p.cycleState === 'damaged') return energyConfig(p.cycleColor, { energyIntensity: 0.55, bloomStrength: 0.7 })
    if (p.isDestroyed) return energyConfig(p.cycleColor, { energyIntensity: 0, coreIntensity: 0, bloomStrength: 0 })
    return energyConfig(p.cycleColor)
  })
}
