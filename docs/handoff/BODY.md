# Body and assembly handoff

Updated 2026-09-30. Read `../REDESIGN_REQUEST.md` completely. Primary reference is
`../references/00_generated_hybrid_concept.png.png`, the riderless board attached by
the user during this session. Reference 01 is riderless side; 03 is front
three-quarter/rider; 05 is rider side; 06 is a rider board. Preserve the originals.
The selected board is a visual target, while established engineering dimensions,
wheel hardware and solved rider contacts remain locked.

## Current source versus built evidence

Pass8 is the current built/captured artifact. See `../review/verification.json`
for exact source/output hashes and results, and `../review/reference-comparison.png`
for the retained review sheet. No human visual approval is recorded.

Compared with pass5, the body now has .66m broad reference shoulders and a tapered
crowned coaming, a true inner wheel-well bridge, a compound waist fitting the rider,
a forward angular band, coaming energy inserts, open reactor cheeks, and a lower
rear haunch. Shared profile interpolation uses monotone tangents. The old .46m
mechanical reference width remains separate so contacts/pivots do not move.
Static body/rider, mechanical envelopes and136-pose canopy sweep pass locally.
Earlier pass4/pass5 findings below are implementation history, not current failures.

## Implemented geometry and continuation ownership

The coordinator owns shared builds and cross-part decisions. Before delegating
new edits, assign one writer per source file; prior subagent names are provenance,
not permission for concurrent changes to that file.

| Parts / files | Current implementation | Continuation owner and next action |
| --- | --- | --- |
| 12 chassis meshes — `tools/geo/chassis.py` | Closed sampled skins replace the original plate stacks. Nose follows the tire circle, includes a fender and closed crown; narrow mid-shell ends at the reactor aperture; raised coaming surrounds the rider channel; rear shoulders share tail boundaries; sill curves upward. | Coordinator / body specialist: review pass8, compare side/front/top mass against reference, then correct silhouette before fine detail. |
| Core, spine, belly, underbody — same file | Forward tub and low reactor cradle leave the center open. Twin spine rails, a graphite saddle liner and three shallow diffuser channels replace exposed support slabs. | Coordinator: verify real loaded clearances, ground line, and whether the liner reads as a recessed seat rather than a raised tray. |
| Rider mount, canopy, back support — `tools/geo/cockpit.py` | Curved saddle substrate, crowned center deck, separate side shoulder skins, curved carbon back pad and conforming canopy-energy strips. `saddle_surface`, `tail_floor`, and `tail_outer` are shared with chassis. | Cockpit specialist after primary boundaries settle; previous implementation by argent_environment_inspector. Inspect closed/open transitions and seam behavior; preserve contacts and hinges. |
| Handlebar/control/chest/shin/foot/display — same file | Existing solved contact builders and functional detail retained. Deploy-arm attachments were independently raised/shortened for the canopy sweep, preserving hinges. | Cockpit specialist: rerun rider/contact checks and inspect full rider-to-shell clearance; do not move the rider solution to accommodate body changes. |
| Body and ancillary energy — `tools/geo/emission.py` | Primary band follows the compound nose with width compensation through the angular shoulder stroke. Secondary and rear inserts follow sill/rear surfaces; reactor emission surrounds the aperture. | Coordinator / emission specialist; previous implementation by reference_geometry_audit. Pass8 band is built and rendered. Inspect continuity in red, alternate hues and lights-off without changing neutral material ownership. |
| Nine detachable panels — `tools/geo/damage.py` | Independent conforming nose/mid/rear patches; reactor cover is an open peripheral annular bezel, not a cap over the core. | Damage specialist after body boundaries settle; previous implementation by reference_geometry_audit. Verify no floating overlays, z-fighting or reactor coverage; animate detachment on the existing pivots. |
| Reactor/rings/core/gyros — `tools/geo/reactor.py` | Core/ring/gyro builders remain intact. Housing changes replace occluding side plates with inner/outer annular lips and six narrow webs per side; cooling fins and parked blades move toward the perimeter. Center remains (.30, 0, .40), with the body aperture based on radius .238. | Coordinator / mechanical reviewer: rebuild and inspect integrated front/rear obliques and macro, then gyro/ring sweep through the newly opened cheeks. An isolated reactor render is not proof of an unobstructed assembled aperture. |
| Wheel rings/bearings/brakes/calipers/suspension/RearDrive — `tools/geo/wheels.py` and dispatch | Existing engineering retained. Regression protects 17 meshes and their parent/pivot ancestry. | Coordinator: rerun `check_preserved_wheels.py` after every canonical rebuild; review reported normal/UV drift in real wheel lighting. Do not alter wheel topology to recover body budget. |
| SteeringYoke and animation origins — `tools/build_lightcycle.py` | Separate repair moves the steering yoke origin to its real pivot at (-.96, 0, .82), with geometry preserved. It is excluded from the wheel baseline for this reason. | Runtime/build specialist; previous repair by runtime_contract_audit. Run the rest-pose regression and inspect steering animation; do not change axle or canopy pivots. |
| Four collision proxies and FX anchors — builder/spec | `COL_LC_Body`, both wheel colliders, `COL_LC_RiderZone`, and all named trail/boost/spark/crash/derez/impact anchors remain declared. | Coordinator / runtime specialist: verify export visibility/ownership and applicability to the revised silhouette; do not equate the sampled shell guard with a full collision-system check. |

`tools/geo/__init__.py` dispatches by contractual node name. The canonical builder
owns material assignment, UV generation, parents, mesh origins and export. Do not
fuse the bike, rename nodes/materials or move shared origins while changing skins.

`chassis.skin()` applies a 64% sampling tier before producing the front/back skin
and perimeter caps. It affects chassis, cockpit, damage and emissive patches but
does not rebuild wheel topology. Profile exported/LOD geometry after changes;
never infer budget compliance solely from the sampling factor.

## Locked measurements and coupled surfaces

Blender is Z-up, nose -X, lateral Y. Wheel centers are X ±.96, Z .46; outer radius
.46 and lateral half-width .15. Nominal envelope is 2.95 × .66 × .98 m (mechanical width remains .46m); ground
clearance is .085 m. Runtime GLB is Y-up. Do not use lateral wheel width as an X
clearance approximation.

Rider X/Z contacts: grip (-.72,.70), chest (-.238,.528), knee (.443,.695), foot
(.62,.28). Leg Y is .21; rider top Z is .796; center-canopy minimum underside is
.856. Its authored roof starts at .864 with .008 backing. Side-canopy hinges
remain at (.62, ±.122636, .755); deploy-arm pivots retain their original solution.

The shared saddle spans X -.105 to .375; its front drops below the torso capsule
and rises to the .695 rear endpoint. A graphite liner sits .0035 above this same
surface. The canopy spans X .495 to 1.115. Fixed rear shoulders end .004 below
`tail_floor(x)`, and `tail_outer(x)` defines their shared lateral seam. Change both
dependants through the shared functions rather than creating detached ribbons.

## Next modeling actions

Review the retained pass8 comparison with the user. Remaining art questions concern
junction continuity, tail root, reactor gyro dominance and reference surface quality.
Preserve the built candidate; make any further changes from this source, not an
old pass. Run body/rider and mechanical guards, rebuild, wheel/texture/rest/sweep
checks, LODs and changed render evidence after each accepted geometry revision.

The fixed rider constraint helper `rider_clearance.py` derives capsules from the
existing solver. It shapes the underside/crown around the rider; it does not move
joints. `check_body_rider.py` independently samples evaluated body surfaces, edges
and triangle centers. Intended contact pads are excluded. Full body-to-canopy and
moving gyro/damage collision proof remains outside these sampled checks.

Current source SHA and exact next task are in HANDOFF/STATUS/TASKS. Update them
at interruptions and never label current technical results as human art approval.
