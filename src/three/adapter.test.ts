/**
 * The one check that has to exist: two players, one asset, no colour bleed.
 * Run: node src/three/adapter.test.ts
 */
import assert from 'node:assert/strict'
import * as THREE from 'three'
import { ThreeLightCycleMaterialAdapter } from './ThreeLightCycleMaterialAdapter.ts'
import { energyConfig } from '../energy/config.ts'

/** Stand-in for the loaded GLB: one shared body material, two emissive channels. */
function fakeCycle(): THREE.Object3D {
  const root = new THREE.Group()
  const named = (name: string) => {
    const m = new THREE.MeshStandardMaterial({ name })
    m.emissiveIntensity = 3
    return m
  }
  const graphite = named('MAT_LC_GRAPHITE')
  for (const [mesh, mat] of [
    ['LC_Body_Core', graphite],
    ['LC_Underbody', graphite], // same material on two meshes, as in the real asset
    ['LC_Wheel_Front_EnergyRing', named('MAT_LC_EMISSIVE_PRIMARY')],
    ['LC_Reactor_Core', named('MAT_LC_EMISSIVE_CORE')],
  ] as const) {
    const o = new THREE.Mesh(new THREE.BoxGeometry(), mat)
    o.name = mesh
    root.add(o)
  }
  return root
}

const matOf = (a: ThreeLightCycleMaterialAdapter, node: string) =>
  (a.root.getObjectByName(node) as THREE.Mesh).material as THREE.MeshStandardMaterial

const source = fakeCycle()
const p1 = new ThreeLightCycleMaterialAdapter(source)
const p2 = new ThreeLightCycleMaterialAdapter(source)

p1.apply(energyConfig('blue'))
p2.apply(energyConfig('gold'))

// 1. Players do not recolour each other.
const blue = matOf(p1, 'LC_Wheel_Front_EnergyRing').emissive.getHexString()
const gold = matOf(p2, 'LC_Wheel_Front_EnergyRing').emissive.getHexString()
assert.notEqual(blue, gold, 'players share an emissive material - multiplayer colour bleed')

// 2. The source asset is never mutated, so a third player still starts clean.
const src = (source.getObjectByName('LC_Wheel_Front_EnergyRing') as THREE.Mesh)
  .material as THREE.MeshStandardMaterial
assert.equal(src.emissive.getHexString(), '000000', 'adapter mutated the loaded GLB')

// 3. Non-emissive materials stay shared - one graphite on the GPU, not one per player.
assert.equal(
  matOf(p1, 'LC_Body_Core'),
  matOf(p2, 'LC_Body_Core'),
  'body material was cloned per player - wastes GPU memory for no reason',
)

// 4. One clone per material name, not per mesh.
assert.equal(matOf(p1, 'LC_Body_Core'), matOf(p1, 'LC_Underbody'))

// 5. Repeated applies must not compound the authored strength.
const before = matOf(p1, 'LC_Reactor_Core').emissiveIntensity
p1.apply(energyConfig('blue'))
p1.apply(energyConfig('blue'))
assert.equal(matOf(p1, 'LC_Reactor_Core').emissiveIntensity, before, 'emissiveIntensity compounds')

// 6. The §18 gate is reachable at runtime and really is zero.
p1.lightsOff()
assert.equal(matOf(p1, 'LC_Wheel_Front_EnergyRing').emissiveIntensity, 0)
assert.equal(matOf(p1, 'LC_Reactor_Core').emissiveIntensity, 0)
assert.equal(matOf(p2, 'LC_Reactor_Core').emissiveIntensity > 0, true, 'lightsOff leaked to player 2')

console.log('adapter: 6/6 ok')
