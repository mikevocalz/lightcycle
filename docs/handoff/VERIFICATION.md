# Verification and continuation

Current pass8 local result: **PASS**, with no human art approval yet. Exact source
hashes, triangle budgets and limitations are in `../review/verification.json`.
Typecheck/tests/build/validate/rider/pack/lods/profile/qa:ci/qa:matrix all ran.
Canonical/packed and all 8 LOD texture checks pass. Rest/clip, wheel, fixed shell,
static body/rider and canopy sweep checks are wired into CI. Remote CI is separate.

LOD0/1/2/3: 298668 / 143658 / 68460 / 29436. Canonical 102 nodes/11 materials/33 clips;
packed keeps 102 names plus 78 optimizer children. Zero errors AND zero warnings.

One coordinator owns shared Blender/GLB/LOD/render outputs. Never run competing
production builders. The current evidence is retained under `docs/review` with
source/output hashes. Prior pass4/5 records are historical diagnostic results.

Use `--factory-startup --python-exit-code 1` for direct Blender calls. Sandbox
Blender startup previously crashed during Metal initialization before Python;
a scoped escalated run succeeded. Diagnose that environment failure from logs,
and check output freshness as well as exit status. Do not repeatedly rerun an
unchanged failing startup or interpret old files as newly generated artifacts.

## Ordered execution after source integration

Use `npm ci` if dependency state changed or is missing. First run source checks
and the bounded rest-pose regression; that regression uses a temporary scene and
does not replace the canonical assets.

```sh
python3 -m compileall -q tools
npm run typecheck
npm test
blender --factory-startup -b --python-exit-code 1 -P tools/check_rest_pose.py
```

Then one coordinator builds and validates the integrated candidate:

```sh
npm run build:glb
npm run validate
python3 tools/check_texture_contract.py assets/export/lightcycle.glb
python3 tools/check_preserved_wheels.py assets/export/lightcycle.glb --report assets/evidence/wheel-preservation-current.json
blender --factory-startup -b assets/source/lightcycle_blockout.blend --python-exit-code 1 -P tools/check_shell_geometry.py
npm run rider
npm run validate:body
npm run validate:canopy
```

Inspect fresh clay and targeted reference views before committing to expensive
full-matrix polish. Use a fresh render directory per pass, as documented in
`QA.md`. If geometry changes again, regenerate the relevant canonical and evidence
artifacts before continuing to final packaging.

```sh
npm run pack
python3 tools/check_texture_contract.py assets/export/lightcycle.runtime.glb --require-ktx2
npm run lods
for lod in 0 1 2 3; do
  python3 tools/check_texture_contract.py "assets/export/lightcycle.lod${lod}.glb"
  python3 tools/check_texture_contract.py "assets/export/lightcycle.lod${lod}.runtime.glb" --require-ktx2
done
npm run profile
npm run qa:ci
npm run qa:matrix
```

`qa:matrix` does not itself compose the requested review sheet. Capture the exact
red/lights-off/alternate-color roster into `assets/render/reference-review`, then
run `npm run qa:comparison`. The composer fails on missing or corrupt inputs and
records source hashes; it does not prove that all supplied images came from the
same build. Check their render receipts before presenting the sheet.

## Per-part verification and continuation ownership

| Area | Required verification / next action | Owner |
| --- | --- | --- |
| Canonical hierarchy/export | Exactly 102 declared nodes/parents, 74 render meshes plus 4 intentional collision meshes and 24 empties; 11 material names; 18 portable + 15 Viro clips; zero validator errors **and zero warnings**. | Coordinator/build specialist. The validator can exit zero with warnings; inspect its report. |
| Body/sill/aperture | Current-source six-view clay inspection; side/front/top mass, wheel integration, rider-channel depth, tail seam and reactor opening. Static shell guard plus full surface/motion inspection. | Body specialist, coordinated with cockpit/damage/emission writers. |
| Wheels and steering | Run canonical wheel baseline check with 1e-6 m geometry tolerance; retain raw/normal/UV diagnostics. Review wheel macro lighting. Independently test corrected SteeringYoke pivot and steering clip. | Coordinator/mechanical reviewer; wheel baseline excludes SteeringYoke only. |
| Reactor/rings/gyros | Preserve centered core/rings/gyros and animation; inspect pass8 open housing cheeks and inspect their webs, relocated cooling/blades, integrated visibility and moving clearance against shell, damage bezel and energy rings. | Mechanical/animation reviewer. Housing geometry is deliberately changed; no dedicated core/ring/gyro fingerprint check currently exists. |
| Cockpit/canopy/rider | Contact targets, canopy underside, rider envelope; inspect deploy/reverse/drive transitions and full canopy sweep against static shoulders. | Cockpit/animation reviewer. Passing endpoint contacts is not a full swept-volume proof. |
| Collision/anchors/damage | Four collision proxies and FX origins remain named/parented; test host ownership, body-envelope applicability, nine panel detachments, spark placements, crash and derez behavior. | Runtime/build specialist. Collider existence does not certify gameplay collision behavior. |
| Rest pose and clip library | `check_rest_pose.py` covers neutral matrices, save/reload/export, all 33 names and the real yoke pivot. Keep tracks/actions discoverable while live NLA evaluation is disabled; inspect actual exported motion separately. | Runtime/build specialist; `rest_pose.py` is shared by builder and renderer. |
| PBR/neutral energy/UVs | Embedded maps and UVs in canonical and all packed/LOD artifacts; no baked player hue; test all six runtime colors and lights-off. Generated AO is not currently attached. Inspect reflections/seams, not only map presence. | Material/runtime specialist; preserve 11 slots and four neutral emission channels. |
| LODs/compression | Native `gltfpack -kn -tc`; validate every canonical/runtime LOD; record actual sizes/counts. Preserve names, pivots and silhouette while reducing detail. | Coordinator/build specialist. |
| Zustand/material adapters | Typecheck/tests for player ownership, neutral strengths, source immutability, namespace isolation, disposal, and lights-off; load the real packed GLB in browser. | Runtime specialist; `src/state`, `src/energy`, `src/three`, `src/viro`. No React `useState`. |
| Ribbon/trail/damage runtime | Preserve Y-up trail sampling, teleport breaks, bounded point buffers, renderer adapters, damage mapping and panel visibility; test host animation/FX integration separately. | Runtime specialist; `src/runtime`, `ThreeLightRibbon`, `ViroLightRibbon`, `ThreeDamageAdapter`. |
| Viro lifecycle / Rive HUD | Preserve one-active-composite-clip transitions and host `onFinish`; retain HUD/leaderboard writer fields. There is no `.riv` artboard or native host app here. | Runtime/host integrator; `ViroAnimationAdapter`, `src/hud/riveBinding.ts`. Do not mark native UI integration complete. |
| Capture/comparison/human review | Complete current-source clay, all-color/view matrix, lights-off and 4×3 reference sheet; document deviations and obtain explicit human reference-fidelity acceptance. | QA coordinator, then user. Human acceptance blocks merge. |
| Quest/PICO/device performance | Actual host/multiple-bike/track/FX frame times, native Viro isolation/transitions, and PICO runtime qualification. Preserve `expo-horizon-core` and the established window contract if an Expo Quest host is later added or changed. | Platform integrator with real host/hardware. Static asset statistics are not FPS. |

LOD budgets remain LOD0 180k–300k, LOD1 ≤150k, LOD2 ≤70k, LOD3 ≤30k. The profile
tool enforces the LOD0 lower bound; do not pad meaningless geometry to satisfy it.
If the policy conflicts with a better model, record that conflict and resolve it
deliberately. Pass8 LOD0 is near the upper bound; measure geometry after every revision. Quest 2 targets local LOD1/remote LOD3; Quest 3
targets local LOD1/remote LOD2. No headset target loads LOD0.

The actual browser check starts with `npm run preview` at
`http://localhost:4173/preview/`. Verify KTX2 decoding, all six colors from one GLB,
lights-off, orbit controls and console/load errors. The preview currently has no
animation selector; exported motion needs a separate playback check. KTX2 decoding passed in the actual pass8 browser check; see retained evidence. Pinned Three imports use esm.sh and
require network access. Synthetic unit tests do not load production geometry or
exercise native Viro.

## Automation gaps and durable evidence

GitHub Actions now invokes rest-pose, wheel preservation, static shell envelopes,
static body/rider, canopy sweep and all canonical/packed/LOD texture checks.
The convenience npm `check` scripts are narrower than the workflow; use the
explicit release commands and workflow for complete coverage. New npm commands:
`validate:wheels`, `validate:body`, `validate:canopy`, `validate:textures`.

Shell reports include source/checker hashes and test 17 selected shell parts;
damage/energy meshes are outside that guard. Body/rider tests sample 17 fixed
non-contact shell parts, and canopy checks 136 poses. These are not continuous
collision tests or body-to-canopy self-collision proof. Wheel normals/UV changes
remain a separate visual review even when geometry is preserved.

Historical CI `12b231f` and old LOD counts 283826/142878/67678/28294 do not validate
the redesign. Keep commands, completed logs, hashes, receipts, failures and exact
remaining actions. No Game Development Studio sealed run/provider receipt is
claimed: its `game-dev` CLI is unavailable in this environment.

Commit coherent source/handoffs and retained evidence, push the existing branch,
and prepare the PR with actual checks and current comparison. Merge only after
technical gates and explicit human reference-fidelity confirmation both pass.
