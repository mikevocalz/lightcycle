# LIGHT CYCLE HANDOFF / RESUME POINT

This file exists so another coding/design session can resume the work without reconstructing the requirements.

## Current design decision

Build **one photoreal AAA / PS5-style Light Cycle** that blends:

- **1982 Syd Mead silhouette / simplicity**
- **TRON: Ares mechanical realism / practical construction**
- **modern high-end game PBR materials, geometry, lighting and animation**

Do not make it cartoonish. Do not make it look like a generic sport bike with neon.

## User-selected player colors

Runtime only — one geometry asset:

- Blue
- Red
- Gold
- Purple
- Green
- White

The physical bike remains graphite / black / metal. The player's color controls the energy system, trail, reactor, wheel energy, FX and UI identity.

## Critical architecture decisions already made

- ONE canonical `lightcycle.glb`
- never duplicate the model per color
- neutral emissive masks
- player-specific material state must be instance-safe in multiplayer
- model is broken into independent named pieces
- separate front/rear wheel assemblies
- central reactor contains multiple independently animated rings / gyros
- rider cockpit and supports stay modular
- rear canopy mechanically transforms for high-speed mode
- damage panels remain separate
- trail is runtime-generated from `LC_FX_TrailOrigin`
- collision uses simplified proxy meshes
- Three.js + Viro share the same semantic asset structure
- renderer-specific adapters translate the shared energy config
- **no React `useState`; Zustand only**

## Do not lose these required nodes

```text
LC_ROOT
LC_Wheel_Front
LC_Wheel_Front_OuterRing
LC_Wheel_Front_InnerRing
LC_Wheel_Front_Bearing
LC_Wheel_Front_EnergyRing
LC_Wheel_Rear
LC_Wheel_Rear_OuterRing
LC_Wheel_Rear_InnerRing
LC_Wheel_Rear_Bearing
LC_Wheel_Rear_EnergyRing
LC_Reactor_Core
LC_Reactor_Ring_A
LC_Reactor_Ring_B
LC_Reactor_Ring_C
LC_Gyro_X
LC_Gyro_Y
LC_Gyro_Z
LC_Canopy_L
LC_Canopy_R
LC_FX_TrailOrigin
LC_FX_Boost
LC_FX_CrashCenter
LC_FX_DerezCenter
```

Full hierarchy is in `LIGHTCYCLE_MASTER_REFERENCE_AND_BUILD_PROMPT.md`.

## Visual quality bar

Before emission:

> The physical bike itself must look like an expensive, believable AAA sci-fi vehicle.

Look for:

- milled precision metal
- carbon/composite surfaces
- material-specific roughness
- real panel depth
- fasteners / service logic
- real wheel mechanisms
- mechanically plausible transformation
- subtle wear rather than post-apocalyptic damage

## Research / references

Primary:

- https://theasc.com/article/making-of-tron-1982/
- https://danielsimon.com/film-design/tron-legacy/
- https://haisuwangdesign.com/tron-dill
- https://julianbell.ca/tron-ares
- https://www.artofvfx.com/tron-ares-david-seager-production-vfx-supervisor-vincent-papaix-and-jeff-capogreco-vfx-supervisors-ilm/

Secondary inspiration:

- https://grafikaone.artstation.com/projects/QzAeJ4
- https://roen911.artstation.com/projects/nEQrE
- https://www.deviantart.com/paul-muad-dib/art/TRON-Ares-Lightcycle-with-silhouette-1239823724

## What is finished in this handoff

- visual direction is locked
- reference categories are identified
- color system is defined
- modular GLB hierarchy is defined
- runtime color strategy is defined
- trail strategy is defined
- reactor behavior is defined
- high-speed transformation concept is defined
- damage/collision concept is defined
- Three.js/Viro portability requirements are defined
- Zustand requirement is preserved
- QA matrix and initial LOD budgets are defined

## What the next session should do

1. Inspect the current game repo and existing Light Cycle implementation before creating anything new.
2. Map existing model nodes to the required hierarchy rather than blindly replacing working assets.
3. Verify current Three.js and Viro animation APIs and current GLB loaders.
4. Create an automated node/material/animation manifest from the GLB.
5. Add CI validation for required nodes and clips.
6. Implement the renderer-independent `LightCycleEnergyConfig`.
7. Implement Three.js material adapter.
8. Implement Viro material adapter.
9. Bind the selected player color from Zustand to bike + FX + Rive HUD.
10. Confirm two simultaneously rendered players can have independent colors.
11. Implement runtime trail origin and collision behavior.
12. Add visual QA scene with all six color variants using the same loaded model.
13. Profile LODs on target devices before locking triangle budgets.

## Exact resume prompt

Copy/paste this into the next implementation session:

> Continue the TRON Light Cycle work from `LIGHTCYCLE_MASTER_REFERENCE_AND_BUILD_PROMPT.md` and `HANDOFF.md`. Do not redesign the architecture. Inspect the repo and current model implementation first. Preserve the single canonical modular GLB, the exact semantic node hierarchy, the six runtime colors, Three.js + Viro portability, independently animated wheels/reactor/canopy/damage pieces, runtime Light Ribbon, and Zustand-only state management. The final visual target is realistic current-generation AAA/PS5 hard-surface quality, not cartoonish or generic cyberpunk. Start by auditing what already exists against the handoff, then implement the smallest missing foundation first and leave a machine-readable status report of completed, partial, blocked and next steps.

