# Light Cycle

One canonical modular `lightcycle.glb`. Six runtime energy colors layered over it.
Three.js on the web, ViroReact in XR, Zustand for state.

The rule everything else serves, from `docs/LIGHTCYCLE_MASTER_REFERENCE_AND_BUILD_PROMPT.md` §18:

> If all emissive lighting is switched off, does the bike still look like an
> exceptionally detailed, believable AAA science-fiction vehicle?

Two ways to ask it: `npm run render:lightsoff` in Blender, and `adapter.lightsOff()`
at runtime. Both zero every emissive channel and leave the machine to stand on its
materials.

## Where things live

| Path | What |
|---|---|
| `spec/lightcycle.spec.json` | materials, colors, clips, canonical dimensions |
| `spec/lightcycle.nodes.json` | the 102-node hierarchy, parents, material assignment |
| `tools/build_lightcycle.py` | builds the modular scene in Blender and exports the GLB |
| `tools/validate_glb.py` | CI gate + manifest generator, no Blender or npm needed |
| `tools/render_matrix.py` | QA renders, including the lights-off shot |
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
