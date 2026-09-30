# LIGHT CYCLE — HANDOFF / RESUME POINT

**Repo:** https://github.com/mikevocalz/lightcycle (public)
**Latest commit:** `88b368f` on `main`
**Updated:** 2026-09-30

This file is the resume contract. It is kept truthful on purpose — if something
is unfinished it says so, because a handoff that overstates progress costs the
next session more than it saves.

---

## ONE-LINE STATE

The engineering foundation and pipeline are complete and green. The **model is
partially migrated to production geometry: 18 of 78 mesh nodes are finished
(both wheel assemblies); 60 are still blockout proxies.** It does not yet pass
the lights-off quality gate.

---

## DESIGN DECISIONS — DO NOT RE-LITIGATE

- ONE canonical `lightcycle.glb`. Never six colored GLBs.
- Node names are **contractual**. `tools/validate_glb.py` fails the build on a rename.
- Runtime reads `spec/` for node roles, never the GLB's `extras`.
- Colors are runtime state. Nothing hued is ever baked into a texture.
- Zustand only. No React `useState` for gameplay state.
- `NeutralToneMapping` in three.js, `AgX` in Blender — ACES desaturates hot golds/reds.
- gltfpack is a **separate step**, never a flag on the Blender export.

---

## HOW THE MODEL MIGRATION WORKS

`tools/geo/` dispatches production builders **per node name**. A node with a
builder gets real geometry; a node without one keeps its blockout proxy. This is
why the asset can be finished assembly-by-assembly without ever breaking the
contract, the validator, the manifest or the two runtime adapters.

To finish an assembly: add a builder module under `tools/geo/`, register the node
names in `tools/geo/__init__.py:build_node`, rebuild, validate, render, commit.

---

## COMPLETE

| Area | State |
|---|---|
| Spec as single source of truth | 102 nodes, 11 materials, 18 clips, 6 colors, locked dimensions |
| Blender build → GLB export | `npm run build:glb`, 102/102 objects |
| GLB contract validation + manifest | `npm run validate`, 0 errors |
| Runtime packing (gltfpack `-kn -tc`) | `npm run pack`, ~42–60% smaller, contract intact |
| KTX2/Basis workflow | native gltfpack 1.3 installed and proven |
| `LightCycleEnergyConfig` | renderer-independent |
| Three.js material adapter | instance-safe, 6/6 tests |
| Viro material adapter | Constant+Add recipe, 5/5 tests |
| Zustand store | players keyed by id, no `useState` |
| Rider ergonomics | 4/4 contacts, `npm run rider` ALL PASS |
| XR LOD budget | Quest 2/3 figures in `spec.xrBudget` |
| **Front + rear wheel assemblies** | **production geometry, 18 nodes** |

## INCOMPLETE — THE ACTUAL REMAINING WORK

| # | Item | State |
|---|---|---|
| 1 | Central reactor geometry | PROXY. Next task. |
| 2 | Chassis + nose/mid/rear shells | PROXY |
| 3 | Cockpit + rider contact surfaces | PROXY |
| 4 | Articulated canopy | PROXY |
| 5 | Damage panel geometry | PROXY |
| 6 | UV unwrap | NOT STARTED (needs final geometry) |
| 7 | PBR texture package | NOT STARTED (needs UVs) |
| 8 | Neutral emissive masks | NOT STARTED |
| 9 | High-poly → runtime bake | NOT STARTED |
| 10 | 16 of 18 animation clips | only `LC_WheelSpin`, `LC_ReactorIdle` exist |
| 11 | LOD1 / LOD2 / LOD3 | NOT STARTED (LOD0 only) |
| 12 | Light Ribbon runtime | NOT STARTED |
| 13 | Damage runtime | NOT STARTED |
| 14 | Derezz runtime | NOT STARTED |
| 15 | Preview app + color picker | NOT STARTED |
| 16 | Rive HUD binding | NOT STARTED |
| 17 | QA render matrix | partial: a few views, 1 of 6 colors |
| 18 | Performance profiling | NOT STARTED |

---

## CURRENT FILES

- Blender source: `assets/source/lightcycle_blockout.blend` (name is now stale — it is a hybrid)
- Canonical export: `assets/export/lightcycle.glb` — 102 nodes, 47,288 tris
- Packed runtime: `assets/export/lightcycle.runtime.glb`
- Geometry builders: `tools/geo/_lib.py`, `tools/geo/wheels.py`, `tools/geo/__init__.py`

## CLIPS

Done: `LC_WheelSpin`, `LC_ReactorIdle`
Remaining 16: `LC_Idle`, `LC_ReactorAcceleration`, `LC_SteerLeft`, `LC_SteerRight`,
`LC_LeanLeft`, `LC_LeanRight`, `LC_Brake`, `LC_BoostEnter`, `LC_BoostLoop`,
`LC_BoostExit`, `LC_HighSpeedTransform`, `LC_HighSpeedReverse`,
`LC_ReactorOverload`, `LC_Damage`, `LC_Crash`, `LC_Derez`

A clip spanning several nodes carries its name on the **NLA track**, with
`export_merge_animation='NLA_TRACK'`. Naming the Action instead produces
`LC_WheelSpin_Rear`-style names the validator rejects.

---

## KNOWN TRAPS (verified empirically — do not rediscover these)

1. **Blender 5.x actions are slotted.** `Action.fcurves` does not exist; fcurves live under `layers → strips → channelbags`.
2. **Blender 5.x Principled sockets**: `Coat Weight`, `Transmission Weight`, `Emission Strength`. The `Clearcoat *` names are gone.
3. **Blender auto-suffixes duplicate object names at assignment time.** The builder hard-fails on collision rather than shipping `LC_Wheel_Front.001`.
4. **Render engine strings** are `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`. `BLENDER_EEVEE_NEXT` raises. AgX look is `AgX - Base Contrast`.
5. **gltfpack default deletes 5 contractual nodes.** Always `-kn`. Blender's `export_gltfpack_kn` defaults False, and its `export_use_gltfpack` writes to a `gltfpacked/` subdir while swallowing `CalledProcessError`.
6. **npm gltfpack cannot do KTX2 at all** (Node/WASM, no BasisU). Use the native build.
7. **`tools/geo/_lib.py:revolve`** authors profiles as (lateral, radius); lateral must lie ALONG the spin axis or rings collapse to ribbons.
8. **Viro has no emissive property**, and `Viro3DObject` cannot address a named sub-node from JS. Material name is the only runtime handle.
9. The local Blender has `io_scene_gfbanm` + BlenderMCP addons that throw a harmless `unregister_class` traceback on every headless exit. Ignore it.

## OPEN QUESTIONS (need hardware / cannot be settled from source)

- Can one `Viro3DObject` run several named clips concurrently on different sub-nodes? `ViroAnimation` is a singular config. **Blocks independent wheel+reactor motion in XR.**
- Does `shaderOverrides` truly isolate per-player material state on device, or does the global registry leak? **The whole XR multiplayer color story rests on this.**
- PICO appears nowhere in the ReactVision platform matrix. Do not claim support.

---

## NEXT TASK

**Build the central reactor in production geometry.** It is the designated hero
detail and the doc requires it to be interesting with emissions OFF.

Create `tools/geo/reactor.py` and register these in `tools/geo/__init__.py`:
`LC_Reactor_Core`, `LC_Reactor_Ring_A/B/C`, `LC_Gyro_X/Y/Z`,
`LC_Reactor_Housing`, `LC_Reactor_Energy`.

Needs nested precision rings, magnetic support yokes, a suspended core, bearing
races, aperture shutters, containment structure and cooling fins. Reuse
`_lib.revolve` and `_lib.radial`.

### Exact next commands

```bash
cd ~/lightcycle
npm run check                      # confirm green baseline first
# author tools/geo/reactor.py, register node names in tools/geo/__init__.py
npm run build:glb
npm run validate
blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --lights-off --view reactor --samples 64
npm run rider                      # must stay ALL PASS
git add -A && git commit && git push
```

---

## RESUME PROMPT

```text
Continue completing the production Light Cycle in:

https://github.com/mikevocalz/lightcycle

Read first:

README.md
docs/HANDOFF.md
docs/STATUS.json
docs/LIGHTCYCLE_MASTER_REFERENCE_AND_BUILD_PROMPT.md
spec/lightcycle.spec.json
spec/lightcycle.nodes.json

Do not restart the project.

Continue from the exact state recorded in HANDOFF.md.

The goal remains a fully finished AAA/PS5-quality TRON 1982 x TRON: Ares Light Cycle.

Do not stop at blockout, scaffolding, documentation, or partial implementation.

Finish the next incomplete production item, run validation, update STATUS/HANDOFF,
commit, push, then continue to the next incomplete item until the complete
definition-of-done checklist is green.
```
