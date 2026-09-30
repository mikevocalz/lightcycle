# Light Cycle

One canonical modular `lightcycle.glb`. Six runtime energy colors layered over it.
Three.js on the web, ViroReact in XR, Zustand for state.

The rule everything else serves, from `docs/LIGHTCYCLE_MASTER_REFERENCE_AND_BUILD_PROMPT.md` §18:

> If all emissive lighting is switched off, does the bike still look like an
> exceptionally detailed, believable AAA science-fiction vehicle?

Two ways to ask it: `npm run pack           # gltfpack -kn -tc -> lightcycle.runtime.glb (60% smaller)
npm run rider          # ergonomics check against a prone rider proxy
npm run check          # build + validate + pack + typecheck + tests
npm run render:lightsoff` in Blender, and `adapter.lightsOff()`
at runtime. Both zero every emissive channel and leave the machine to stand on its
materials.

## Where things live

| Path | What |
|---|---|
| `spec/lightcycle.spec.json` | materials, colors, clips, canonical dimensions |
| `spec/lightcycle.nodes.json` | the 102-node hierarchy, parents, material assignment |
| `tools/build_lightcycle.py` | builds the modular scene in Blender and exports the GLB |
| `tools/validate_glb.py` | CI gate + manifest generator, no Blender or npm needed |
| `tools/pack_runtime.py` | gltfpack step producing the compressed runtime GLB |
| `tools/rider_proxy.py` | anthropometric rider + ergonomics check (doc §15) |
| `tools/render_matrix.py` | QA renders, including the lights-off shot |
| `src/viro/` | Viro adapter and its multiplayer-safety test |
| `src/energy/config.ts` | `LightCycleEnergyConfig` — renderer-independent |
| `src/three/` | Three.js adapter and its instance-safety test |
| `src/state/cycleStore.ts` | Zustand store, no `useState` |
| `docs/STATUS.json` | what is done, partial, blocked and next |

The two spec files are the single source of truth. Node names, material names and
clip names appear there once; the Blender build, the validator, the manifest and
both renderer adapters all read them. Editing a name anywhere else is a bug.

## Commands

```bash
npm run build:glb     # Blender -> assets/export/lightcycle.glb
npm run validate      # contract check + manifest
npm run typecheck
node src/three/adapter.test.ts
npm run pack           # gltfpack -kn -tc -> lightcycle.runtime.glb (60% smaller)
npm run rider          # ergonomics check against a prone rider proxy
npm run check          # build + validate + pack + typecheck + tests
npm run render:lightsoff
blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --color gold --view reactor
```

## State of the asset

The geometry is a **blockout**. Every contractual node exists at the right size
and pivot wearing the real material library, and the whole pipeline runs end to
end — but the mesh inside each node is still a primitive proxy, and it does not
pass the §18 gate yet.

That is the point of the structure: modelling replaces the proxy mesh inside a
node without touching its name, so the adapters, the validator and the manifest
keep working the whole way through. See `docs/STATUS.json`.

## Contract

`tools/validate_glb.py` fails the build on any of these:

- a node named in `HANDOFF.md` as must-not-lose is renamed or missing
- a node's parent does not match the spec (a right name on a wrong pivot)
- a material or animation clip appears that the spec does not declare
- a material's `emissiveFactor` is non-neutral — that means a player hue got
  baked into the asset, and runtime color switching is dead

## gltfpack

Packing is a separate step on purpose. Run with its defaults, gltfpack deletes
five contractual nodes — `LC_Reactor_Core`, `LC_FX_TrailOrigin`, `LC_FX_Boost`,
`LC_FX_CrashCenter`, `LC_FX_DerezCenter` — and the validator fails. `-kn` keeps
all 102 names with correct parenting, but Blender's `export_gltfpack_kn` defaults
to `False`, so wiring gltfpack into the export would ship a broken asset quietly.
Blender also writes to a `gltfpacked/` subdirectory and swallows the subprocess
error, reporting success on a failed pack.

Use the **native** binary from
[zeux/meshoptimizer releases](https://github.com/zeux/meshoptimizer/releases).
The npm package is a Node/WASM build with no BasisU support and cannot produce
KTX2 at all.

## Viro parity

`ViroMaterial` has no emissive property of any kind, and `Viro3DObject` cannot
address a named sub-node from JS. Material name is the only runtime handle,
which is why every independently-controlled region gets its own material slot in
the canonical GLB. `ViroMaterials` is one global name-keyed registry, so each
player mints uniquely-suffixed names or two bikes share a colour. Clearcoat,
anisotropy, transmission and IOR are absent — the XR build reads flatter than
the web one. See `src/viro/ViroLightCycleMaterialAdapter.ts`.
