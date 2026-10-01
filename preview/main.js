import * as THREE from 'https://esm.sh/three@0.186.1'
import { GLTFLoader } from 'https://esm.sh/three@0.186.1/examples/jsm/loaders/GLTFLoader.js'
import { KTX2Loader } from 'https://esm.sh/three@0.186.1/examples/jsm/loaders/KTX2Loader.js'
import { RoomEnvironment } from 'https://esm.sh/three@0.186.1/examples/jsm/environments/RoomEnvironment.js'
import { OrbitControls } from 'https://esm.sh/three@0.186.1/examples/jsm/controls/OrbitControls.js'

const spec = await fetch('../spec/lightcycle.spec.json').then((r) => r.json())
const host = document.querySelector('#app')
const status = document.querySelector('#status')
const colors = document.querySelector('#colors')

const scene = new THREE.Scene()
scene.background = new THREE.Color('#05070a')
const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.01, 100)
camera.position.set(-3.4, 1.6, 3.6)

const renderer = new THREE.WebGLRenderer({ antialias: true })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.setSize(innerWidth, innerHeight)
renderer.toneMapping = THREE.NeutralToneMapping
renderer.toneMappingExposure = 1.15
host.append(renderer.domElement)
// Metal and clearcoat need reflected surroundings, including in lights-off QA.
const pmrem = new THREE.PMREMGenerator(renderer)
const studio = new RoomEnvironment()
scene.environment = pmrem.fromScene(studio, 0.04).texture
studio.dispose()
pmrem.dispose()

const controls = new OrbitControls(camera, renderer.domElement)
controls.target.set(0, 0.48, 0)
controls.enableDamping = true

scene.add(new THREE.HemisphereLight('#d8e5ff', '#08090a', 1.8))
const key = new THREE.DirectionalLight('#ffffff', 5.2)
key.position.set(-2.5, 3, 4)
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
    // Collision proxies remain in the GLB contract but are never visible art.
    if (o.name.startsWith('COL_')) { o.visible = false; return }
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

// npm run preview serves the repository root, including the version-locked
// Basis transcoder installed by npm ci. Runtime GLBs use KTX2/BasisU textures.
const ktx2Loader = new KTX2Loader()
  .setTranscoderPath('../node_modules/three/examples/jsm/libs/basis/')
  .detectSupport(renderer)

new GLTFLoader().setKTX2Loader(ktx2Loader).load(
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

// Opt-in, read-only diagnostics for repeatable local QA; no scene handles escape.
if (new URLSearchParams(location.search).has('qa')) {
  Object.defineProperty(window, '__lightcycleQA', { value: () => {
    const proxies = []
    cycle?.traverse((o) => { if (o.name.startsWith('COL_')) proxies.push({ name: o.name, visible: o.visible }) })
    return {
      loaded: !!cycle,
      proxies,
      materials: [...emissive].map(([name, mats]) => ({ name, colors: [...new Set(mats.map((m) => m.emissive.getHexString()))], intensities: [...new Set(mats.map((m) => m.emissiveIntensity))] })),
      glbRequests: performance.getEntriesByType('resource').filter((r) => r.name.endsWith('.glb')).length,
      draws: renderer.info.render.calls,
      triangles: renderer.info.render.triangles,
    }
  } })
}
