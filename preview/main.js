import * as THREE from 'https://esm.sh/three@0.186.1'
import { GLTFLoader } from 'https://esm.sh/three@0.186.1/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'https://esm.sh/three@0.186.1/examples/jsm/controls/OrbitControls.js'

const spec = await fetch('../spec/lightcycle.spec.json').then((r) => r.json())
const host = document.querySelector('#app')
const status = document.querySelector('#status')
const colors = document.querySelector('#colors')

const scene = new THREE.Scene()
scene.background = new THREE.Color('#05070a')
const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.01, 100)
camera.position.set(-3.4, 1.8, -3.6)

const renderer = new THREE.WebGLRenderer({ antialias: true })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.setSize(innerWidth, innerHeight)
renderer.toneMapping = THREE.NeutralToneMapping
renderer.toneMappingExposure = 1.15
host.append(renderer.domElement)

const controls = new OrbitControls(camera, renderer.domElement)
controls.target.set(0, 0.48, 0)
controls.enableDamping = true

scene.add(new THREE.HemisphereLight('#d8e5ff', '#08090a', 1.8))
const key = new THREE.DirectionalLight('#ffffff', 5.2)
key.position.set(-2.5, -3, 4)
scene.add(key)
const rim = new THREE.DirectionalLight('#8bbcff', 3.2)
rim.position.set(2.6, 3.2, 2)
scene.add(rim)

const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(30, 30),
  new THREE.MeshStandardMaterial({ color: '#07090c', metalness: 0.65, roughness: 0.28 }),
)
floor.rotation.x = -Math.PI / 2
scene.add(floor)

const emissive = new Map()
let cycle = null

function register(root) {
  root.traverse((o) => {
    if (!o.isMesh) return
    const mats = Array.isArray(o.material) ? o.material : [o.material]
    for (const m of mats) {
      if (!m?.name?.startsWith('MAT_LC_EMISSIVE_')) continue
      if (!emissive.has(m.name)) emissive.set(m.name, [])
      emissive.get(m.name).push(m)
    }
  })
}

function applyColor(name) {
  document.querySelectorAll('button[data-color]').forEach((b) => {
    b.dataset.active = String(b.dataset.color === name)
  })
  if (name === 'off') {
    for (const mats of emissive.values()) for (const m of mats) m.emissiveIntensity = 0
    status.textContent = 'LIGHTS OFF — §18 material validation'
    return
  }
  const c = spec.colors[name]
  for (const [materialName, mats] of emissive) {
    const def = spec.materials[materialName]
    const hex = def.channel === 'core' ? c.core : c.energy
    for (const m of mats) {
      m.emissive.set(hex)
      m.emissiveIntensity = def.emissionStrength
      m.toneMapped = false
      m.needsUpdate = true
    }
  }
  status.textContent = name.toUpperCase() + ' · same GLB, materials only'
}

for (const name of Object.keys(spec.colors)) {
  const b = document.createElement('button')
  b.dataset.color = name
  b.textContent = name
  b.style.color = spec.colors[name].energy
  b.onclick = () => applyColor(name)
  colors.append(b)
}
const off = document.createElement('button')
off.dataset.color = 'off'
off.textContent = 'lights off'
off.onclick = () => applyColor('off')
colors.append(off)

new GLTFLoader().load(
  '../assets/export/lightcycle.runtime.glb',
  (gltf) => {
    cycle = gltf.scene
    scene.add(cycle)
    register(cycle)
    applyColor('blue')
  },
  undefined,
  (error) => {
    console.error(error)
    status.textContent = 'Build first: npm run build:glb && npm run pack'
  },
)

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(innerWidth, innerHeight)
})

renderer.setAnimationLoop(() => {
  controls.update()
  renderer.render(scene, camera)
})
