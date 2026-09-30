import assert from 'node:assert/strict'
import { LightRibbonPath } from './trail.ts'
import { damageRuntime } from './damage.ts'
import { bindLightCycleHud, lightCycleHudModel, type RiveViewModelWriter } from '../hud/riveBinding.ts'
import type { Player } from '../state/cycleStore.ts'

const trail = new LightRibbonPath({ minDistance: 0.1, teleportDistance: 2 })
assert.equal(trail.append({ x: 0, y: 0, z: 0 }, 0), true)
assert.equal(trail.append({ x: 0.02, y: 0, z: 0 }, 16), false, 'sub-threshold trail point was kept')
assert.equal(trail.append({ x: 0.2, y: 0, z: 0 }, 32), true)
assert.equal(trail.segments().length, 1)
trail.append({ x: 4, y: 0, z: 0 }, 48)
trail.append({ x: 4.2, y: 0, z: 0 }, 64)
assert.equal(trail.segments().length, 2, 'teleport failed to split the wall')

const player: Player = {
  playerId: 'p1',
  playerName: 'MCP',
  cycleColor: 'purple',
  cycleState: 'damaged',
  speed: 72,
  boost: 0.4,
  health: 0.42,
  isDestroyed: false,
}
const damaged = damageRuntime(player)
assert.equal(damaged.clip, 'LC_Damage')
assert.equal(damaged.detachedNodes.length > 0, true)
assert.equal(damaged.energyMultiplier < 1, true)

const destroyed = damageRuntime({ ...player, cycleState: 'destroyed', isDestroyed: true, health: 0 }, 0.8)
assert.equal(destroyed.clip, 'LC_Derez')
assert.equal(destroyed.detachedNodes.length, 9)
assert.equal(destroyed.energyMultiplier, 0)
assert.equal(destroyed.derezProgress, 0.8)

const writes: Record<string, unknown> = {}
const writer: RiveViewModelWriter = {
  setString: (k, v) => { writes[k] = v },
  setNumber: (k, v) => { writes[k] = v },
  setBoolean: (k, v) => { writes[k] = v },
  setColor: (k, v) => { writes[k] = v },
}
bindLightCycleHud(writer, lightCycleHudModel(player, 12))
assert.equal(writes.playerName, 'MCP')
assert.equal(writes.score, 12)
assert.equal(writes.damaged, true)
assert.match(String(writes.playerColor), /^#[0-9A-F]{6}$/)

console.log('runtime: 12/12 ok')
