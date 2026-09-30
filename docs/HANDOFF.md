# LIGHT CYCLE — HANDOFF / RESUME POINT

**Repo:** https://github.com/mikevocalz/lightcycle  
**Branch:** `finish/production-lightcycle` / PR #1  
**Verified head:** `12b231ff99ce7ab93160334ba549cbd24a46ad7a`  
**Updated:** 2026-09-30

## ONE-LINE STATE

The production Light Cycle software/asset pipeline is complete and green. There are
**74 production render mesh nodes and 4 intentional collision proxies; there are
no remaining render blockout proxies.** The latest full
`production-asset-verify` GitHub Actions run passed.

## VERIFIED PRODUCTION STATE

- one canonical modular GLB; six runtime energy colors
- 102 contractual nodes, 11 materials
- 18 portable clips + 15 Viro composite compatibility clips = 33 exported clips
- 74 production render meshes, UV-unwrapped
- neutral PBR + neutral emissive texture package generated deterministically
- canonical build validates with 0 errors / 0 warnings
- runtime KTX2/BasisU pack validates with 0 errors / 0 warnings
- latest runtime pack: 12,543,484 → 4,572,460 bytes (64% smaller)
- rider ergonomics: all checks pass
- LOD0: 283,826 tris
- LOD1: 142,878 tris
- LOD2: 67,678 tris
- LOD3: 28,294 tris
- Three.js multiplayer material adapter tests pass
- Viro material isolation tests + composite animation mapping pass
- runtime Light Ribbon implemented for Three.js and Viro
- damage/derezz runtime mapping implemented
- Rive HUD/leaderboard data binding implemented
- six-color one-GLB preview implemented
- QA renderer supports the full six-color/eight-view matrix + lights-off
- CI smoke renders 20 views and uploads all build evidence

## IMPORTANT RENDERER DECISION

Viro's embedded GLB animation playback is treated as one active clip at a time.
Do **not** try to layer the portable wheel/reactor/state clips on Viro. The asset
exports 15 `LC_Viro_*` composite compatibility clips and
`src/viro/ViroAnimationAdapter.ts` maps gameplay state into them. Three.js keeps
the independent clips.

## DESIGN DECISIONS — DO NOT RE-LITIGATE

- ONE canonical `lightcycle.glb`; never six colored GLBs.
- Runtime color only; player hue is never baked into textures.
- Node names are contractual.
- Zustand only for gameplay/player state; no React `useState`.
- Three.js uses NeutralToneMapping; Blender authoring QA uses AgX.
- gltfpack stays a separate post-process and always preserves named nodes.
- Runtime/glTF/Three/Viro coordinates are Y-up; Blender authoring coordinates are Z-up.
- The 4 `COL_LC_*` meshes are intentional invisible collision proxies.

## FULL LOCAL / CI COMMANDS

```bash
npm ci
npm run typecheck
npm test
npm run build:glb
npm run validate
npm run rider
npm run pack
npm run lods
npm run profile
npm run qa:ci       # CI-sized verification subset
npm run qa:matrix   # full six-color/eight-view render matrix
npm run preview     # http://localhost:4173/preview/
```

## WHAT IS STILL HARDWARE-ONLY

These are not source-code blockers and must not be marked as unfinished modeling:

1. **Quest device profiling** — confirm real frame time with track, FX and multiple bikes.
2. **Viro native multiplayer isolation** — prove player material namespaces stay isolated on device.
3. **Viro animation lifecycle** — verify the composite clips transition cleanly in the host `Viro3DObject`.
4. **PICO qualification** — do not claim PICO support until the target runtime/device is profiled.
5. **Human art-direction review** — inspect the full `npm run qa:matrix` output at final shipping exposure/settings.

## RESUME RULE

Do not restart or remodel the bike from scratch. If future work is requested,
start from the current production geometry and contracts. New work should be
device integration, art-direction polish, or host-game integration—not replacing
the finished pipeline.
