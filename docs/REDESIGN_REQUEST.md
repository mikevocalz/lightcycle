Use these skills throughout this task:

[$build-3d-game-rooms]
[$game-development-studio]
[$game-asset-production]

REPO:
https://github.com/mikevocalz/lightcycle

GOAL:
FIX THE CURRENT LIGHT CYCLE MODEL.

Do NOT start over.
Do NOT throw away the engineering/runtime work that is already correct.
Do NOT redesign the wheels unless necessary for body-to-wheel integration.

The current production model is technically complete, but its BODY DESIGN DOES
NOT MATCH THE APPROVED REFERENCE IMAGES.

The wheels are the only major area that currently looks close enough.

The body must now be substantially redesigned to match the attached reference
images much more closely.

============================================================
NON-NEGOTIABLE VISUAL TARGET
============================================================

The attached reference images are the visual authority.

The finished model must look like the bike shown in those references:

- extremely low, long Light Cycle silhouette
- huge front and rear wheel masses
- continuous sculpted black body shell
- broad automotive-quality compound surfaces
- aggressive front wheel fairing
- strong wedge-shaped front side body
- narrow integrated cockpit
- sweeping seat/top-body line
- sculpted tail over/into rear wheel
- central mechanical reactor intentionally visible
- body panels that FLOW into one another
- dark premium carbon / painted composite / milled metal
- broad TRON energy shapes integrated into the body
- realistic current-generation AAA / PS5 vehicle quality
- looks expensive even when all emissive lighting is OFF

TARGET DESIGN FORMULA:

1982 TRON LIGHT CYCLE SILHOUETTE
+
TRON: ARES MECHANICAL REALISM
+
THE ATTACHED REFERENCE BODY SURFACING
+
PS5/AAA HERO VEHICLE QUALITY

The current result is NOT acceptable as the visual target.

It currently looks too much like:

- an exposed prototype chassis
- lots of independent mechanical brackets
- a skeletal machine
- thin disconnected panels
- a generic futuristic motorcycle
- procedural boxes with detailing attached

That must change.

============================================================
MOST IMPORTANT RULE
============================================================

DO NOT confuse DETAIL with DESIGN.

Adding more bolts, vents, ribs, brackets, fasteners, or tiny mechanical pieces
will NOT fix the model.

The problem is the LARGE PRIMARY SURFACES AND SILHOUETTE.

Fix the large body masses first.

At thumbnail distance the bike should already resemble the reference.

Only after the silhouette and primary surfaces are correct should secondary
mechanical detail be added.

============================================================
KEEP THESE PARTS
============================================================

Preserve the current wheel engineering unless a minor adjustment is required:

- front tire
- rear tire
- hubless architecture
- inner wheel rings
- bearings
- brake hardware
- wheel energy rings
- wheel pivots
- wheel animation
- current wheel scale
- wheel runtime color behavior

The wheels are the strongest current area.

Also preserve:

- central reactor architecture where useful
- contractual GLB node naming
- all runtime animation contracts
- collision proxies
- Light Ribbon implementation
- damage/derezz runtime
- Rive bindings
- Three.js adapter
- Viro adapter
- LOD pipeline
- texture pipeline
- KTX2 pipeline
- Zustand state architecture
- one-model/six-runtime-color system

DO NOT break working systems to fix the art.

============================================================
BODY REDESIGN — PRIMARY PASS
============================================================

Rebuild the visible body around the existing mechanical foundation.

The current chassis/body builders should be considered replaceable visual
geometry while preserving their contractual node identities.

Focus on:

LC_Body_Core
LC_Body_Spine
LC_Belly
LC_Nose_Shell_L
LC_Nose_Shell_R
LC_Mid_Shell_L
LC_Mid_Shell_R
LC_Rear_Shell_L
LC_Rear_Shell_R
LC_Underbody
LC_Armor_L
LC_Armor_R

The visible shell should no longer read as a collection of disconnected thin
rectangular plates.

------------------------------------------------------------
1. FRONT BODY / NOSE
------------------------------------------------------------

This is currently one of the biggest misses.

Look closely at the attached references.

The front wheel needs a substantial sculpted fairing/body volume around and
behind it.

Create a strong aerodynamic front mass that:

- partially embraces the front wheel
- flows rearward from the wheel
- has a deep sculpted shoulder
- visually anchors the front half of the machine
- creates the large black surface visible in side profile
- supports the large angular energy feature from the reference
- transitions smoothly into the central body

The body immediately behind the front wheel should have the visual weight of a
real hero vehicle.

It must NOT be a tiny plate attached to a frame.

The reference has a bold wedge-like side composition.

Recreate that design logic.

------------------------------------------------------------
2. LARGE FRONT SIDE ENERGY SHAPE
------------------------------------------------------------

The reference uses a VERY IMPORTANT broad energy graphic around the front body.

It is not a tiny LED strip.

It creates a strong diagonal/angular visual shape roughly following:

upper front body
→ diagonal downward stroke
→ lower body continuation

This is one of the strongest identifying features in the reference.

Add a dedicated neutral emissive geometry region for this.

It must use the existing runtime energy-color architecture.

Do NOT bake red/blue/gold/etc into the model.

The same geometry must support:

blue
red
gold
purple
green
white

at runtime.

------------------------------------------------------------
3. MAIN CENTER BODY
------------------------------------------------------------

The center needs MUCH more coherent body surfacing.

The reference has a long continuous side body that visually joins the front
wheel region to the reactor/rear structure.

Build large sculpted surfaces first.

Use:

- long tension lines
- shallow concave transitions
- tapered surfaces
- controlled panel breaks
- recessed technical sections
- flush access panels
- layered aerodynamic surfaces

Avoid:

- box + bolt + box + bolt repetition
- random louvers everywhere
- excessive exposed scaffolding
- tiny repeated brackets becoming the dominant visual language

The side silhouette must feel deliberately styled.

------------------------------------------------------------
4. CENTRAL REACTOR PRESENTATION
------------------------------------------------------------

The reactor should remain visible like the reference.

It should read as a deliberate circular mechanical/energy assembly integrated
into the body—not as a random component exposed because bodywork is missing.

Create a shaped body opening around it.

Think:

BODY SHELL
→ purpose-built circular/arched mechanical aperture
→ reactor visually framed inside
→ surrounding conduits / structural members visible
→ body resumes behind it

The reactor should become a HERO DETAIL.

Do NOT bury it.

Do NOT leave the surrounding region empty.

------------------------------------------------------------
5. TOP LINE / RIDER AREA
------------------------------------------------------------

The reference has a very specific top silhouette.

The current model does not.

Create a continuous visual line that flows from:

front body
→ cockpit/control region
→ rider torso/seat channel
→ raised rear deck
→ tail

The rider should look INSERTED INTO the machine.

Do not make it look like a conventional motorcycle seat sitting on top.

The cockpit should be narrow and integrated.

Controls can remain mechanically detailed, but the major shell forms around
them must be clean.

------------------------------------------------------------
6. SEAT / COCKPIT CHANNEL
------------------------------------------------------------

Match the visual logic of the reference:

- recessed rider channel
- sculpted surfaces around rider
- low torso position
- very low center of gravity
- body rises around parts of the rider rather than leaving everything exposed
- smooth transitions around chest support / back support
- no normal sportbike fuel tank
- no normal motorcycle saddle silhouette

Maintain all ergonomics tests.

The bike moves around the rider solution; do not invalidate the solved contact
points.

------------------------------------------------------------
7. REAR BODY / TAIL
------------------------------------------------------------

The current rear is too exposed and skeletal.

The reference has a much stronger integrated tail/body volume.

Create:

- upper tail shell
- sculpted rear shoulders
- body surfaces leading toward the rear wheel
- controlled cutouts revealing suspension/mechanics
- a sharp futuristic trailing upper edge
- smooth transition from rider seat to rear deck
- stronger body-to-rear-wheel relationship

The rear wheel should still be visually dominant, but it should feel like it
belongs to the body.

------------------------------------------------------------
8. UNDERBODY
------------------------------------------------------------

Make the bottom silhouette cleaner.

The reference has a continuous purposeful lower line.

Use an aerodynamic structural undertray with:

- subtle diffuser geometry
- protected mechanical routing
- clean body termination
- enough ground clearance
- visual continuity between front body, reactor region, and rear

Do not let the bottom become a forest of tiny parts.

============================================================
SURFACE LANGUAGE
============================================================

The body needs REAL COMPOUND CURVATURE.

Do not fake the final design entirely with cubes.

Use proper hard-surface modeling techniques:

- controlled subdivision surfaces where appropriate
- bevelled hard-surface forms
- spline/curve-driven profiles where useful
- lofted sections
- purposeful booleans
- clean supporting topology
- shaped wheel arches
- tapered thickness
- chamfered body edges
- intentional highlight lines
- automotive surfacing

The reference is NOT flat.

The body must generate clean sweeping reflections.

This is crucial.

============================================================
MATERIAL BREAKDOWN
============================================================

Maintain the neutral runtime architecture.

Primary body:
- premium black painted composite
- gloss/satin material contrast
- strong clearcoat reflections
- subtle roughness variation

Structural exposed areas:
- carbon composite
- milled aluminum
- dark anodized metal
- brushed metal

Wheel/contact:
- realistic dark synthetic tire

Energy:
- neutral white authored emissive mask
- player hue at runtime only

Do not cover every surface in carbon weave.

Use carbon where structurally sensible.

============================================================
REFERENCE PRIORITY
============================================================

Use the attached reference images in this exact priority:

1. SIDE PROFILE / BODY SILHOUETTE
2. TOP PROFILE
3. FRONT / REAR WIDTH
4. FRONT FAIRING SHAPE
5. SEAT + TAIL FLOW
6. BODY-TO-WHEEL RELATIONSHIP
7. CENTRAL REACTOR FRAMING
8. ENERGY GRAPHIC PLACEMENT
9. SMALL DETAIL

Do NOT prioritize the existing procedural body's shape over the approved refs.

The existing model is implementation history, not the visual authority.

============================================================
SILHOUETTE GATE
============================================================

Before adding fine detail, create renders with:

- flat neutral clay material
- no emissive lighting
- side orthographic
- front orthographic
- rear orthographic
- top orthographic
- front 3/4
- rear 3/4

Compare them DIRECTLY to the attached references.

Stop the modeling pass if the silhouette still clearly differs.

The SIDE VIEW is the most important.

At small thumbnail size:

REFERENCE
vs
NEW MODEL

should clearly read as the same design family.

Do not continue polishing an incorrect silhouette.

============================================================
LIGHTS-OFF GATE
============================================================

Render the entire machine with ALL energy materials at zero intensity.

The bike must still look like:

- a premium current-generation sci-fi vehicle
- an intentional production design
- a sophisticated hard-surface asset

Not:

- a gray blockout
- a pipe frame
- a collection of brackets
- a machine dependent on neon to look interesting

============================================================
MODEL MODULARITY
============================================================

Do NOT fuse the asset into one mesh.

Keep the existing contractual hierarchy.

Maintain all animation/damage nodes.

Moving parts must continue to use correct physical pivots.

Damage panels must remain detachable.

Canopy parts must remain independently animatable.

Do not rename nodes casually.

tools/validate_glb.py MUST stay green.

============================================================
WHEEL-TO-BODY TRANSITIONS
============================================================

This deserves special attention.

The current wheel detail is substantially stronger than the body.

Do not downgrade the wheels.

Instead, make the BODY rise to the same quality level.

Around the front wheel:

- body/fairing should closely frame the tire mass
- maintain realistic clearance
- build actual inner wheel-well structure
- hide meaningless empty space
- provide clean shell termination

Around the rear:

- body should taper into structural framing around the rear wheel
- use intentional negative space
- expose selected mechanics rather than everything

============================================================
CENTRAL REACTOR QA CAMERA
============================================================

Fix the current reactor QA render.

The existing reactor close-up is misframed and largely shoots body panels.

Update `tools/render_matrix.py` so:

`--view reactor`

actually centers the complete reactor assembly.

The shot should clearly show:

- reactor core
- concentric rings
- mechanical housing
- surrounding body aperture
- visible conduits
- emissive state

Also add a reactor lights-off capture.

============================================================
FULL QA CONTACT SHEET
============================================================

After the redesign, generate a proper comparison sheet with:

TOP ROW:
- approved reference side
- new model side
- new model front 3/4

SECOND ROW:
- front
- top
- rear

THIRD ROW:
- front wheel detail
- reactor detail
- rear wheel detail

FOURTH ROW:
- lights off side
- lights off 3/4
- alternate runtime energy color

The sheet should make mismatches painfully obvious.

Do not judge only by individual glamour renders.

============================================================
DO NOT BREAK EXISTING SYSTEMS
============================================================

After geometry work, rerun all existing validation:

npm run typecheck
npm test
npm run build:glb
npm run validate
npm run rider
npm run pack
npm run lods
npm run profile
npm run qa:ci
npm run qa:matrix

Everything previously green must remain green.

============================================================
LOD REQUIREMENTS
============================================================

The redesign cannot destroy the XR budget.

Maintain:

LOD0 <= ~300k
LOD1 <= 150k
LOD2 <= 70k
LOD3 <= 30k

Current verified values are approximately:

LOD0: 283,826
LOD1: 142,878
LOD2: 67,678
LOD3: 28,294

The high-poly authoring model can exceed this, but generated runtime LODs must
respect the budgets.

Do not achieve LOD targets by destroying the main silhouette.

============================================================
KEEP CROSS-PLATFORM BEHAVIOR
============================================================

One model must continue working across:

- Three.js
- ViroReact / ReactVision
- Quest XR
- web
- mobile where applicable

The model remains one canonical modular source.

No renderer-specific duplicate bike designs.

============================================================
STATE ARCHITECTURE
============================================================

Keep Zustand.

NO React `useState` for gameplay/player-cycle state.

Preserve:

player identity
energy color
boost
damage
destroyed state
trail
HUD
scoreboard integrations

============================================================
COLOR ARCHITECTURE
============================================================

DO NOT create separate models for:

blue
red
gold
purple
green
white

One GLB.

One material-mask architecture.

Runtime changes color.

The broad front body energy shape, wheels, reactor, tail, cockpit and Light
Ribbon must all derive from the same player color identity.

============================================================
WHAT NOT TO DO
============================================================

Do NOT:

- simply add more detail to the existing wrong body
- preserve incorrect body geometry because it already exists
- change the wheels dramatically
- create a normal motorcycle with neon
- make it skeletal
- make it cartoonish
- make it low-poly-looking
- use random sci-fi greebles to hide bad surfacing
- add thousands of tiny bolts before fixing silhouette
- fuse everything together
- break animation pivots
- rename contractual nodes
- bake player color
- create six GLBs
- replace Zustand with useState
- declare success from CI alone

============================================================
DEFINITION OF DONE
============================================================

Do not call this finished until:

[ ] Side silhouette closely follows the attached approved reference.
[ ] Front fairing has the same strong visual mass as the reference.
[ ] Main body is sculpted and continuous rather than skeletal.
[ ] Large angular front energy feature exists.
[ ] Center body flows naturally around the reactor.
[ ] Reactor is clearly framed as a hero component.
[ ] Seat/cockpit channel looks integrated.
[ ] Rear deck/tail flows cleanly into rear wheel region.
[ ] Top view resembles the approved reference proportions.
[ ] Front/rear widths look intentional.
[ ] Wheels retain their existing strong quality.
[ ] Lights-off render still looks premium.
[ ] All player colors still work from one GLB.
[ ] Rider ergonomics still pass.
[ ] Damage pieces remain separate.
[ ] Animation pivots remain correct.
[ ] GLB validator = 0 errors / 0 warnings.
[ ] LOD budgets still pass.
[ ] Three.js tests pass.
[ ] Viro tests pass.
[ ] Runtime tests pass.
[ ] QA matrix regenerated.
[ ] Reference-vs-model comparison sheet produced.
[ ] Human visual comparison confirms the model actually resembles the references.

============================================================
WORKFLOW
============================================================

1. Audit current `main`.
2. Read README.md, HANDOFF.md, STATUS.json and the master reference document.
3. Inspect the current QA renders.
4. Treat the attached reference images as the visual authority.
5. Preserve wheel/mechanical/runtime work.
6. Produce corrected body silhouette first.
7. Render clay orthographics.
8. Compare directly against refs.
9. Correct silhouette until it matches.
10. Build final hard-surface body.
11. Integrate reactor/cockpit/rear detailing.
12. Re-UV/retexture changed parts.
13. Rebuild canonical GLB.
14. Regenerate all LODs.
15. Run complete verification.
16. Generate reference comparison contact sheet.
17. Update STATUS/HANDOFF truthfully.
18. Commit and push.
19. Open PR.
20. Merge only after all technical checks are green AND the new renders visibly
    match the attached references.

DO NOT STOP AFTER WRITING A PLAN.

DO THE MODELING WORK.

The previous pass proved that a technically green pipeline is not enough.
VISUAL REFERENCE FIDELITY IS NOW A BLOCKING GATE.