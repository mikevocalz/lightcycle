# PASS9 OVERRIDE — EXACT THREE-VIEW REFERENCES REJECTED PASS8

The user explicitly rejected pass8 on 2026-09-30: it does not resemble the newly supplied exact side/front/rear references closely enough. Do not cite pass8 visual evidence as approval. The exact uploaded views now override the older generated collage wherever they disagree. See `docs/handoff/REFERENCE_MEASUREMENTS_2026-09-30.md`.

Pass9 changes the visible proportion contract: longer wheelbase, much smaller hub void, wider wheel sections, broader front/rear body masses, exact front cowl/twin energy rails, rear structural hoop and central rear blade. Runtime node names, one-GLB/six-color behavior, animation ownership, adapters and damage modularity remain constraints. Keep PR #2 draft until fresh CI and explicit human visual approval.

# Light Cycle — resumable reference-body redesign

Updated 2026-09-30. Branch: `art/reference-body-redesign`.
Draft PR: https://github.com/mikevocalz/lightcycle/pull/2 (unmerged; visual approval pending).
Production base: `c5d0039fcbaafa0d77f37c97525ca0f8be079f13`.

## Start here on every resume

Read this file, `STATUS.json`, `handoff/TASKS.json`, the assigned part's handoff,
and `REDESIGN_REQUEST.md`. Inspect git status and preserve existing work. Continue
the first unfinished dependency-ready task; do not restart the model or treat
older technical completion as visual approval. Use bounded subagents with one
writer per file; one coordinator owns shared Blender/GLB/LOD/render outputs.

The user requests durable handoffs for **all parts** and actual modeling work.
Handoffs survive context loss; they cannot make a terminated agent run by itself.
Update this checkpoint and the task ledger before any interruption.

## Current outcome

Pass8 is built, packed, rendered and locally verified. It is a **review candidate,
not an accepted final design**. The user rejected the earlier shape and supplied
`references/00_generated_hybrid_concept.png.png`, the latest white board. They
explicitly confirmed: **match the reference's visible shape; preserve current
wheels**. Do not adopt its printed dimensions by resizing/re-spacing the wheels.
Reference02 remains supporting context. See `handoff/REFERENCE_FIT.md`.

The candidate adds a broader wedge, real wheel-well bridge, compound center waist,
raised/tapered/crowned cockpit coaming, neutral angular energy and cockpit inserts,
framed open reactor housing, shaped tail and sill, and fitted detachable panels.
Body width is .66m; `mechanicalWidth: .46` preserves contact positions, hinges,
damage pivots and collision proxies. Wheel builders and protected geometry remain.

Important fixes: material maps are now attached; saved NLA pose contamination is
removed without dropping clips; steering yoke pivot is physical; canopy skirts
and deploy attachments clear the fixed rider during the sampled transform sweep.
The actual browser preview now decodes KTX2, hides collision proxies and supplies
studio reflections. All colors change materials on the same loaded GLB.

## Durable review and verification

- [4×3 reference comparison](review/reference-comparison.png)
- [Full-resolution renders and receipts](review/renders/)
- [Six clay views and receipts](review/clay/)
- [Browser red](review/browser-red.png), [lights off](review/browser-off.png)
- [Verification, hashes and limitations](review/verification.json)
- [Browser material/resource evidence](review/browser-qa.json)

Current source SHA-256: `5d031623a66d7e45393d59b1952c3ba45c069b9debf8a3f37c913c9450045e32`.
Canonical GLB SHA-256: `6b3425f4488801abe73884b1df045b150668a0cd00ae6fb05d55bb2a306fb6a0`.
Generated GLBs/textures/raw renders are ignored; rebuild commands reproduce them.
Selected review images, receipts, source blend and regression baselines are tracked.
Do not confuse a current source edit with a rebuilt artifact: compare hashes.

Local results: typecheck/tests, build/validate, rider, pack, all LODs, static
profile, qa:ci (20), qa:matrix (63), six clay views and comparison all pass execution.
Canonical has 102 nodes, 11 materials, 33 clips; packed assets keep all contractual
names and may add 78 unnamed optimizer children. Zero validator errors/warnings.
LOD counts: **298668 / 143658 / 68460 / 29436** (all below 300k/150k/70k/30k).
Canonical, packed and all LOD texture checks pass. Rest regression restores 102
nodes and exports 33 clips. Static body/rider and mechanical guards pass; canopy
sweep passes 136 sampled poses. These are sampled checks, not continuous collision
or canopy-to-body self-collision proof.

Wheel geometry/parent/pivot regression passes17 meshes/22 nodes/109712 triangles;
max position delta1.33e-7m. Normal drift up to3.65° and changed UVs remain explicit
shading-review items; do not claim byte-identical shading.

Remote production CI **passed** on `58ac572a23cee1239e8d3a2c8c8ff9d58430a22e`: [run 36754410085](https://github.com/mikevocalz/lightcycle/actions/runs/36754410085). The clean Linux run rebuilt and validated canonical/packed/LOD assets, passed runtime, texture, wheel and rider/canopy checks, rendered all 20 QA views and uploaded production evidence. [Retained receipt](review/ci-run.json). The final checkpoint commit changes handoff documentation/evidence only; inspect latest PR checks before merge.

## Unfinished gates and exact next action

1. **Visual fidelity remains open.** Inspect the comparison honestly. Primary
   review concerns are panel junctions, remaining rail-like cockpit edges, tail
   root continuity, reactor gyro dominance and automotive-quality surfacing.
   The reference family is the target; technical success does not certify it.
2. A concrete comparison was sent to the user for approval or revision. If they
   request changes, refine those primary shapes, rebuild and regenerate affected
   evidence. Do not add decorative detail to hide a wrong silhouette.
3. Draft PR #2 is committed, pushed and open. Keep it draft/unmerged while visual
   review is pending. Full production CI passed; inspect current PR check state on resume. Merge
   only after both technical checks and explicit human visual confirmation.
4. Native Viro/Quest/PICO host/device behavior and FPS remain unverified because
   no native host or headset is present. Rive is a binding interface, not .riv art.

## Per-part continuation

| Part/workstream | Handoff | Implementation |
| --- | --- | --- |
| Chassis/nose/waist/aperture/sill/undertray | [BODY](handoff/BODY.md) | tools/geo/chassis.py |
| Rider channel/canopy/deploy arms/contact points | [BODY](handoff/BODY.md), [RUNTIME](handoff/RUNTIME.md) | tools/geo/cockpit.py, rider_clearance.py |
| Wheel engineering/pivots | [RUNTIME](handoff/RUNTIME.md) | wheels.py, check_preserved_wheels.py, retained baseline |
| Reactor/damage/energy | [BODY](handoff/BODY.md) | reactor.py, damage.py, emission.py |
| Animation/collision/GLB/textures/Three/Viro/Zustand/ribbon/damage/Rive | [RUNTIME](handoff/RUNTIME.md) | exact file map inside |
| Clay/cameras/reference comparison | [QA](handoff/QA.md) | render_matrix.py, compose_comparison.py |
| LODs/pack/checks/CI/release gates | [VERIFICATION](handoff/VERIFICATION.md) | build_lods.py, profile_asset.py, workflow |
| Skills and inspected environment | [SKILLS](handoff/SKILLS.md), [ENVIRONMENT](handoff/ENVIRONMENT.json) | no repeated inspection needed |
| Dependencies/next action | [TASKS](handoff/TASKS.json) | coordinator updates |

Blender crashes during sandbox Metal startup; scoped escalated runs with
`--factory-startup --python-exit-code 1` succeed. `game-dev` CLI is absent; no
provider job or receipt is claimed. Existing Blender/npm pipeline was used.

Fresh-session prompt:

> Read AGENTS.md and docs/HANDOFF.md. Continue the first unfinished task in
> docs/handoff/TASKS.json on the existing branch. Preserve the current wheels and
> working runtime, use the recorded skills and bounded subagents, update all
> checkpoints, and do not declare visual completion or merge without approval.

QA processes are stopped. Scoped Argent cleanup released only chromium-cdp-9222;
the isolated Chrome profile and localhost server created by this task were closed.
No mobile device or user Metro/browser session was changed. Restart `npm run preview`
for interactive review after `npm ci`/packing as needed.
