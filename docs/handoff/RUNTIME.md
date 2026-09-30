# Runtime, material and export handoff

Updated 2026-09-30. This document covers the preserved engineering contracts and
the bounded material/preview repairs discovered during the body-redesign audit.
Read `docs/HANDOFF.md` first for the current overall task and integration state.
The requested visual redesign remains unfinished until its reference comparison
and human visual gates pass; historical technical CI success is not art approval.

## Current pass8 results (supersede historical diagnostics below)

All required local checks pass; exact hashes/results live in `docs/review/verification.json`.
Previously reported static shell/rider intersections are corrected and checked by
`check_body_rider.py`. The rebuilt canonical canopy sweep passes 136 sampled poses.
The browser decodes packed KTX2, hides all 4 collision proxies, changes six colors
on one GLB request, and sets all 4 emission channels to 0 in lights-off mode.
RoomEnvironment supplies physical reflections; the key light is above the Y-up
floor. `?qa=1` enables a read-only `window.__lightcycleQA()` diagnostic snapshot.

Packed GLBs keep102 contractual named nodes and add78 unnamed optimizer children;
180 total nodes is expected after this packing stage. Latest wheel geometry passes,
normal drift up to3.65 degrees and UV changes remain visible review items.
Body `width=.66` is separated from `mechanicalWidth=.46`; all existing actuator,
contact and damage pivot calculations use the latter. User explicitly chose shape
matching while preserving current wheels. No app-window configuration was changed.

## Audit baseline and evidence

- Source audited at `origin/main` commit `c5d0039` before redesign edits.
- The earlier `docs/STATUS.json` reports CI success at `12b231f`, 102 contractual
  nodes, 11 materials, 33 clips, and LOD counts 283,826 / 142,878 / 67,678 / 28,294.
  These are historical baseline claims, not new verification of the redesign.
- The old status contains both early and later pack-size figures. Recompute all
  sizes from the final integrated artifact instead of copying either figure.
- Source inspection found `attach_texture_maps()` defined but never called by
  `build_materials()`. Generated files therefore did not guarantee embedded maps.
- `preview/main.js` loaded the KTX2 runtime asset without configuring KTX2Loader.
  The installed Three GLTFLoader requires that loader for required Basis textures.
- The initial texture-contract check against the existing, pre-rebuild local
  `assets/export/lightcycle.glb` failed with 21 missing physical-material texture
  slots and 23 missing UV attributes. This is a reproduced regression; it does
  not describe a subsequently rebuilt asset.

## Changes made in this workstream

1. `tools/build_lightcycle.py` now calls its existing `attach_texture_maps()` for
   every material. Physical base-color, roughness, metallic and normal maps are
   attached. The exporter combines roughness/metallic into glTF's PBR map.
2. The four energy materials retain neutral scalar emission. Generated white
   masks remain provenance assets; wiring them over Emission Color would defeat
   Blender QA tinting. No hue, strengths, material names or texture designs changed.
3. `preview/main.js` imports the same pinned Three 0.186.1 KTX2Loader, calls
   `detectSupport(renderer)`, and provides it to GLTFLoader. Basis transcoder
   files resolve from `../node_modules/three/examples/jsm/libs/basis/`, served
   by the repository-root `npm run preview` server after `npm ci`.
4. `tools/check_texture_contract.py` checks the exported artifact, following all
   seven physical materials' base-color/metallic-roughness/normal references into
   embedded image bytes and checking UV attributes. It also requires the four
   authored energy factors to remain nonzero and neutral. `--require-ktx2`
   additionally checks packed image references and KTX2 signatures.

Targeted syntax verification passed: Python compile for the builder/checker and
`node --check preview/main.js`. The coordinating agent owns full builds and final
artifact validation; record its results in the main handoff and evidence ledger.
Do not infer positive artifact verification from these syntax checks.

Generated AO maps are currently not attached by the existing texture helper;
this repair does not claim to add AO baking or change material design.

## Rest-pose and steering-pivot regression

The pass3 clay top view exposed a separate pre-existing animation defect. Source
hash `8b1f1970ca791172b5a984b05f0f16110b40267133267ee7ca1a42232812526f`
contained 223 unmuted NLA tracks on 27 animated objects. The clip library was
evaluated as a simultaneous NLA stack at frame 1. Exit/steer clips intentionally
start displaced, so frame 1 is not a neutral pose:

- `LC_SteeringYoke` inherited -0.42 radians around Z from
  `LC_Viro_DriveSteerRight`. Its world-origin pivot made it swing away from the
  vehicle; evaluated bounding-box Y extended from +0.274 to +0.509 m. This was
  the floating rectangular top-view part, not the controls or cockpit display.
- `LC_Canopy_L/R` inherited opposite 1.15-radian rotations and `LC_RearCanopy`
  moved -0.115 m in X from the high-speed exit pose. These contaminated the rear
  silhouette and camera bounds.
- Merely disabling/muting NLA did not restore the saved, already evaluated local
  transforms. Explicit restoration is required.

`tools/rest_pose.py` captures each node's local basis matrix in `lc_rest_matrix`
before `author_clips()` runs. The builder then disables NLA evaluation, clears
the active action and restores recorded matrices before saving/exporting. It
keeps all tracks, strips and actions; strips remain unmuted. The ACTIONS exporter
discovers these clips even when `animation_data.use_nla` is false. The QA renderer
restores the recorded pose before camera bounds and records a restoration receipt.
Old sources without these records must be rebuilt; do not silently guess rest
from an arbitrary animation frame. Packed GLB extras may still be stripped safely:
this metadata belongs to Blender authoring/QA, not a runtime dependency.

`production_pivot('LC_SteeringYoke')` now uses its actual hardware center:
`(-wheelbase/2, 0, wheelRadius + hubRadius + 0.09)`, currently `(-0.96, 0, 0.82)`.
Moving the origin preserves the visible mesh at rest and makes steering rotate
around the yoke rather than the world origin. Wheel geometry/pivots are unchanged.

The lightweight regression below passed in Blender 5.2.1: it reproduced the
overlapping clips, restored 102 nodes across frame changes/save/reload, retained
all 33 exact clip names in a temporary GLB, and verified the exported yoke has
neutral rotation. It uses the real yoke builder and production animation/export
functions; no shared production outputs are written. Full pass4 asset validation
and fresh rest-pose renders remain the coordinating agent's subsequent gates.

```bash
blender --factory-startup -b --python-exit-code 1 -P tools/check_rest_pose.py
```

The rest-pose regression also reads actual exported animation samples: all five
canopy/arm/group channels preserve portable/Viro endpoint parity and
Enter→Loop→Exit continuity. Missing rest records are rejected. These checks pass;
preserved clip names alone would not prove preserved motion.

## Canopy/rider sweep repair and remaining body clearance work

Restoring the neutral pose exposed a second, independent defect in the reshaped
canopy. A read-only audit of source blend
`8f7578be92470cefc6f014789ccb4f5ad900d29af2e7b5e5f7d0275a4a30f8a3`
isolated one high-speed clip at a time. At the closed pose, side-canopy surfaces
penetrated the original finite thigh cylinders by 24.0 mm and the left deploy
arm penetrated the shin cylinder by 10.4 mm. The static contact/canopy-center
check in `rider_proxy.py` does not test this sweep.

The fixed rider, hinge pivots, parent slide, animation keys and crown/top profile
remain unchanged. `cockpit.py` now recedes only the lower leading skirt edge (up
to 225 mm, tapering to zero at the upper seam) and shortens/raises deploy-arm
attachments to keep the knee clear. The rider script gained only a `__main__`
guard so tests can import its authoritative solver without running its UI build.

`tools/check_canopy_sweep.py` checks the seven real, bevel-evaluated canopy meshes
at 136 poses: every frame of portable/composite entry and exit, neutral pose, and
three held-loop samples. It tests vertices, triangle centers and edge midpoints
against conservative rounded capsules from the existing rider solver, with a
2 mm required margin. It records source hashes and, when used on a loaded file,
the input blend hash. It writes no canonical assets. Run either the lightweight
source fixture or the final rebuilt canonical source:

```bash
blender --factory-startup -b --python-exit-code 1 -P tools/check_canopy_sweep.py -- --out /tmp/canopy-source-check.json
blender --factory-startup -b assets/source/lightcycle_blockout.blend --python-exit-code 1 -P tools/check_canopy_sweep.py -- --out assets/evidence/canopy-sweep.json
```

The source-fixture check passed with the current monotone-Hermite body profiles:
closest margins were canopy L/R 5.406/5.418 mm and deploy arm L/R 5.490/8.025 mm.
This result used chassis hash
`fa5e3bd47064bf2b9d0fb59047d1d8809bde58437f512f9f93828279b3bb7743`.
The coordinating agent must rerun against final rebuilt geometry. This sampling
is not a continuous-collision or canopy-to-body self-collision proof.

A separate static rider probe of that same chassis hash found substantial
intersections in the spine, mid/nose shells and foot region of the rear shells;
the body core cleared the probe. The parent owns corrections. Do not use this
canopy PASS to imply the entire body clears the rider. Exact witness coordinates
were sent to the parent and the temporary report is
`/tmp/lightcycle-static-rider-probe.json`; final durable body evidence must be
regenerated after those corrections.

CI now runs the lightweight rest/clip regression before the canonical build,
then wheel preservation, fixed-shell mechanical envelopes and the canopy rider
sweep against the rebuilt asset. It also checks canonical/packed/LOD textures.
The uploaded artifact includes `assets/evidence/`. A local regression PASS does
not mean the remote CI workflow has run or passed.

## Runtime file map and stable contracts

| Files | Preserve |
| --- | --- |
| `spec/lightcycle.spec.json` | One canonical model, six colors, 11 material slots, authored strengths, dimensions, clips, LOD/XR budgets |
| `spec/lightcycle.nodes.json` | 102 named nodes and their parents; 74 render meshes, 4 intentional collision proxies and 24 empties |
| `src/energy/config.ts` | Renderer-independent energy/core/halo identity, channel mapping, `ENERGY_OFF` |
| `src/state/cycleStore.ts` | Zustand player state keyed by player ID; no React `useState` |
| `src/three/ThreeLightCycleMaterialAdapter.ts` | Player-owned emissive clones, shared physical materials, source scene immutability, owned-resource disposal |
| `src/viro/ViroLightCycleMaterialAdapter.ts` | Namespaced global-registry materials; unlit additive energy fallback |
| `src/viro/ViroAnimationAdapter.ts` | One-active-clip composite states; transitions advance through host `onFinish` |
| `src/runtime/trail.ts` | Y-up history, teleport breaks, sampling threshold, bounded points |
| `src/three/ThreeLightRibbon.ts` | Runtime-generated wall/core geometry, energy application, disposal |
| `src/viro/ViroLightRibbon.ts` | Polygon/polyline descriptors and player-namespaced trail materials |
| `src/runtime/damage.ts` | Health/destroyed mapping, nine detachable panels, spark anchors, energy degradation |
| `src/three/ThreeDamageAdapter.ts` | Per-instance panel visibility; host owns animation playback |
| `src/hud/riveBinding.ts` | HUD/leaderboard view-model field names and writer interface |

There is no `.riv` artboard or complete native host app in this repository. The
bindings/adapters are integration contracts, not evidence of completed device UI.

Three.js keeps 18 independent clips. Viro uses 15 `LC_Viro_*` composites because
embedded GLB playback supports one active animation at a time. Do not layer the
portable clips on Viro or create renderer-specific copies of the bike.

Runtime/glTF is Y-up, forward -X. Blender authoring is Z-up, lateral Y. Wheel
rotation about Blender Y maps to glTF Z. Keep wheel geometry, scale and axle
pivots intact while replacing body surfaces.

Keep `LC_Emit_BodyPrimary` on `MAT_LC_EMISSIVE_PRIMARY` for the broad front energy
graphic. The existing contract already provides a dedicated neutral region.
Preserve all nine `LC_Damage_*` meshes as separate detachable pieces, and keep
canopy parts independently animated. Do not fuse the model or add unregistered
named nodes/materials to work around visual-design changes.

Three uses NeutralToneMapping; Blender QA uses AgX. Viro lacks matching clearcoat,
anisotropy, transmission and IOR controls, and approximates energy using Constant
+ Add diffuse. Visual parity must be assessed on its renderer.

## Rider and platform constraints

The body moves around the solved rider. Preserve the existing contact targets in
`spec.dimensions_m.riderEnvelope` and rerun `npm run rider` after relevant edits.
Blender X/Z pairs: grip (-0.72, 0.70), chest (-0.238, 0.528), knee (0.443, 0.695),
foot (0.62, 0.28). Rider top Z is 0.796, required canopy Z is 0.856, and legs run
outboard at Y=0.21. Wheelbase is 1.92 m; wheel diameter 0.92 m; section 0.30 m.

This is an asset/runtime repository, with no Expo host configuration currently
present. When a Meta Quest Expo/React Native host is added or modified, preserve
or integrate `expo-horizon-core`, keep app-window dimensions separate from scene
objects, preserve established orientation and manifest metadata, and ask before
changing an established window contract. These requirements do not authorize
inventing an app-window configuration merely to modify bike geometry.

## Build, LOD and compression ownership

- `tools/build_lightcycle.py`: material setup, production dispatch, UV unwrap,
  pivots, 18 portable + 15 Viro clips, canonical `.blend`/GLB.
- `tools/generate_textures.py`: deterministic neutral texture package.
- `tools/pack_runtime.py`: native `gltfpack -kn -tc`, then contract validation.
  Never omit `-kn`: the optimizer otherwise drops contractual named nodes. Keep
  packaging separate from Blender export. Node extras are DCC bookkeeping.
- `tools/lod_export.py`: applies bevels before measurement and decimation. LOD1/2
  protect small/emissive/damage parts; LOD3 simplifies more parts but keeps names.
- `tools/build_lods.py`: deletes stale output before every LOD export, requires
  fresh output, validates, then packs and validates each runtime LOD.
- `tools/profile_asset.py`: static file/triangle report, not headset FPS proof.

Maintain LOD0 180k–300k, LOD1 <=150k, LOD2 <=70k, LOD3 <=30k. Preserve silhouette
when reducing geometry. Quest 2 uses local LOD1/remote LOD3; Quest 3 uses local
LOD1/remote LOD2. No headset target loads LOD0. PICO remains unqualified.

Only one agent should run shared builds/render generation at a time: they write
the same `assets/source`, `assets/export`, `assets/textures/generated` and render
outputs. Generated GLBs, textures and renders are mostly ignored by Git; durable
evidence needs explicit paths/retained artifacts, not a claim that a commit
contains all build output.

## Verification and continuation

After the integrated geometry/material build, run:

```bash
npm ci
python3 -m compileall -q tools
npm run typecheck
npm test
npm run build:glb
npm run validate
python3 tools/check_texture_contract.py assets/export/lightcycle.glb
npm run rider
npm run pack
python3 tools/check_texture_contract.py assets/export/lightcycle.runtime.glb --require-ktx2
npm run lods
npm run profile
npm run qa:ci
npm run qa:matrix
```

Apply the texture checker to generated LODs as well before final delivery. The
ordinary GLB validator returns zero exit status even when warnings exist; the
redesign acceptance criterion requires both zero errors **and zero warnings**.

Existing `npm test` suites use synthetic Three geometry, a mocked Viro registry,
and runtime mapping assertions. They cover instance color isolation, authored
strength stability, lights-off, composite clip selection, trail splitting,
damage mapping, and Rive writes. They do not load the production GLB, inspect
embedded textures, exercise the browser preview or prove native Viro behavior.

Once packed output exists, start `npm run preview` and verify successful texture
decoding, all six colors from the same asset and lights-off in the actual browser.
The current preview imports Three from esm.sh, so module loading also needs
network access. A static syntax pass does not establish browser success.

Outstanding hardware gates remain: Quest frame time with track/FX/multiple bikes,
native Viro multiplayer material isolation, Viro composite transition lifecycle,
and PICO runtime/device qualification. Outstanding art gates remain in the main
handoff: reference silhouette, clay views, reactor framing, lights-off quality,
full color matrix, comparison sheet and human visual approval. Never mark any of
those passed solely because the technical pipeline is green.

## Canonical wheel preservation regression

`tools/check_preserved_wheels.py` protects 17 existing engineering meshes: front
and rear OuterRing, InnerRing, Bearing, EnergyRing, BrakeDisc, both Calipers,
Suspension, and RearDrive. It additionally checks their named parent chains and
local transforms, including both axle pivots (22 total contract nodes). The
SteeringYoke is explicitly excluded because its pre-existing world-origin pivot
is repaired independently. It is not an ancestor of the protected wheel meshes.

`docs/handoff/WHEEL_BASELINE.json` records the original canonical artifact built
from `c5d0039fcbaafa0d77f37c97525ca0f8be079f13`, before the body redesign, with only
the existing physical-texture attachment hook enabled. Original GLB SHA-256:
`517807eb1da8289601a658ffff53e0b5509fd52e12a9773d0c8a3cb7d044628d`.
The original capture path was `/private/tmp/lightcycle-baseline.glb`; the retained
JSON includes compressed triangle-corner positions/normals and hashes, so future
checks do not depend on that temporary GLB surviving. Do not regenerate this
baseline from a redesigned candidate simply to make a failing check pass.

Run against the **uncompressed canonical** export after each body build:

```bash
python3 tools/check_preserved_wheels.py assets/export/lightcycle.glb --report assets/evidence/wheel-preservation-current.json
```

The hard gate checks oriented triangle surfaces and counts, material-slot names,
attribute ownership, parents, and local transforms. It tolerates reordered
vertices/triangles and UV-seam vertex duplication only when the indexed surfaces
still match. A 10-micrometre position grid establishes triangle correspondence;
every matched corner then undergoes a stricter **1e-6 m maximum measured Euclidean
displacement** check. Unmatched triangles fail. Material and pivot contracts
must match exactly. This gate does not apply to decimated or packed GLBs.

Every report also retains the raw accessor differences and separately compares
per-corner normals and UVs. Normal drift above the default 1e-5 component
diagnostic threshold or changed UVs produces `shading_review_required: true`.
A geometry/contract pass does **not** certify unchanged shading or count as human
visual approval. The recorded normal angle normalizes both vectors before taking
their angular difference; it is distinct from the maximum component delta.

Verified candidate SHA-256 on 2026-09-30:
`da4cb097af9fe4e2ed256fad1db31f75226f83d1efa81402847bd20bea25b95e`.
Results in `assets/evidence/wheel-preservation-current.json`:

- **Geometry and contract PASS:** all 109,712 oriented triangles correspond;
  maximum measured position displacement `1.3328003749250113e-7 m`, below `1e-6 m`.
  All protected materials, parents, and pivots match the original baseline.
- **Shading review pending:** ten protected meshes have normal drift, maximum
  component delta `0.056094199419021606`, maximum actual angle `3.6456095649894853°`.
  Twelve primitive UV layouts changed. The report preserves 59 raw accessor
  differences, including vertex counts/index streams associated with seam splits.
- Baseline self-check passes with zero drift. Targeted in-memory checks prove
  vertex reindexing/duplication are accepted, changed position or axle pivot is
  rejected, and normal/UV changes remain visible diagnostics.

The earlier `assets/evidence/wheel-preservation-pass3.json` is preserved as an
initial raw-accessor diagnostic for candidate `57fb49f0...`; its strict failure
preceded indexed-surface comparison and is not the current geometric verdict.
Re-run the current checker after later rebuilds; do not carry the recorded
candidate hash forward as evidence for different bytes. No source `.blend` or
GLB was modified by this regression work.
