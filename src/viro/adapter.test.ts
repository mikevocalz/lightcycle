/** Run: node src/viro/adapter.test.ts */
import assert from 'node:assert/strict'
import { ViroLightCycleMaterialAdapter, type ViroMaterialDef } from './ViroLightCycleMaterialAdapter.ts'
import { energyConfig } from '../energy/config.ts'

/** Stands in for Viro's global, name-keyed material registry. */
const registry: Record<string, ViroMaterialDef> = {}
const viroMaterials = { createMaterials: (d: Record<string, ViroMaterialDef>) => Object.assign(registry, d) }

const p1 = new ViroLightCycleMaterialAdapter('mike', viroMaterials)
const p2 = new ViroLightCycleMaterialAdapter('alex', viroMaterials)
p1.apply(energyConfig('blue'))
p2.apply(energyConfig('gold'))

// 1. The registry is global, so two players must never collide on a name.
const shared = p1.materialNames().filter((n) => p2.materialNames().includes(n))
assert.deepEqual(shared, [], 'players share a material name - the global registry would bleed colour')

// 2. Both players' materials coexist in the one registry.
for (const n of [...p1.materialNames(), ...p2.materialNames()]) assert.ok(registry[n], `${n} missing`)

// 3. Energy is unlit and additive, or it would take scene lighting and read as paint.
const one = registry[p1.materialNames()[0]!]!
assert.equal(one.lightingModel, 'Constant')
assert.equal(one.blendMode, 'Add')

// 4. Colours actually differ between players.
const c1 = registry[`MAT_LC_EMISSIVE_PRIMARY${p1.ns}`]!.diffuseColor
const c2 = registry[`MAT_LC_EMISSIVE_PRIMARY${p2.ns}`]!.diffuseColor
assert.notEqual(c1, c2, 'blue and gold resolved to the same colour')

// 5. lightsOff must drop out of the bloom pass, not just go dim - a "dark" bike
//    that still glows faintly defeats the whole gate.
p1.lightsOff()
for (const n of p1.materialNames()) {
  assert.equal(registry[n]!.diffuseColor, '#000000')
  assert.equal(registry[n]!.bloomThreshold, 1.0, 'lightsOff left the surface feeding bloom')
}
assert.notEqual(registry[`MAT_LC_EMISSIVE_PRIMARY${p2.ns}`]!.diffuseColor, '#000000',
  'lightsOff leaked to the other player')

console.log('viro adapter: 5/5 ok')
