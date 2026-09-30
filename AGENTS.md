# Project instructions and continuation

Read `docs/HANDOFF.md`, `docs/STATUS.json`, `docs/handoff/TASKS.json`, the assigned
part's `docs/handoff/` document, and `docs/REDESIGN_REQUEST.md` on every resume.
The latter preserves the full user brief and supersedes older art-complete claims.
Continue unfinished work on the current branch; never restart the asset. Inspect
uncommitted changes and live processes before acting. Preserve work from other agents.

Update HANDOFF, STATUS and TASKS at each meaningful checkpoint and before ending.
Record source files, commands/results, evidence, remaining defects, active process
IDs, dependencies and the exact next action. Historical results need a commit.
A started command is not a passed check. Do not fabricate visual/human approval.
Handoffs survive context loss; they cannot keep a terminated process running.

Use bounded subagents with disjoint source-file ownership. One coordinator owns
shared Blender/GLB/LOD output generation. Recreate agent assignments on resume if
the old processes no longer exist. Commit/push/open-PR are authorized by the brief;
merge requires green technical checks AND human reference-fidelity confirmation.

The user-attached board matches `docs/references/00_generated_hybrid_concept.png.png`.
Treat it as primary visual authority. Preserve wheels, hierarchy, names, pivots,
animations, collisions, damage modularity and one-GLB/six-color runtime contracts.
Large sculpted surfaces and silhouette precede detail. Read the full brief.

Required skills: build-3d-game-rooms, game-development-studio,
game-asset-production. Paths, scope and conditional routes: `docs/handoff/SKILLS.md`.

## Spatial application configuration

For Expo/React Native applications targeting Meta Horizon/Quest, integrate
`expo-horizon-core` and preserve its configuration. Keep app window width/height
separate from size/position of objects inside a Viro/XR scene. Do not change
established window dimensions or orientation while adjusting scene objects.
Preserve `orientation: 'default'` when configured. Ask before changing an
established window contract. Use appropriate configuration for other headsets.

When modifying native/config plugins, preserve platform-specific manifest metadata
and layout entries through prebuild. Merge entries rather than replacing another
plugin's manifest. Verify merged manifests and intended platform build variants.
Add a regression check for configuration loss. Never claim other apps were audited
without inspecting them.

## React state

Always use Zustand for React application/component state; never introduce React
`useState`. For per-instance state retain a vanilla Zustand store in a ref or memo
and subscribe with selectors. Keep native resources and imperative handles in refs;
do not persist them in serialized application state.
