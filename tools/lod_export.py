#!/usr/bin/env python3
"""Export one Light Cycle LOD from the generated production .blend.

Run under Blender:
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/lod_export.py -- --lod 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())

TARGETS = {
    0: None,
    1: 150_000,
    2: 70_000,
    3: 30_000,
}


def tri_count():
    total = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.name.startswith("COL_"):
            continue
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def decimate_to(target: int):
    before = tri_count()
    if before <= target:
        print(f"LOD target {target:,}: source already {before:,}; no decimation required")
        return before, before

    # Leave tiny mechanical/emissive parts alone; collapse larger surfaces enough
    # to reach the scene target while preserving the node/pivot contract.
    candidates = []
    fixed = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.name.startswith("COL_"):
            continue
        o.data.calc_loop_triangles()
        tris = len(o.data.loop_triangles)
        if tris < 96 or "Energy" in o.name or o.name.startswith("LC_Emit_"):
            fixed += tris
        else:
            candidates.append((o, tris))

    variable = sum(t for _, t in candidates)
    wanted_variable = max(1, target - fixed)
    ratio = max(0.035, min(1.0, wanted_variable / max(1, variable)))

    for o, tris in candidates:
        m = o.modifiers.new("__LC_LOD_DECIMATE__", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = ratio
        if hasattr(m, "use_collapse_triangulate"):
            m.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.modifier_apply(modifier=m.name)
        o.select_set(False)

    after = tri_count()
    print(f"LOD decimate: {before:,} -> {after:,} tris (ratio {ratio:.3f}, target <= {target:,})")
    return before, after


def export(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_extras=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_merge_animation="NLA_TRACK",
        export_nla_strips=True,
        export_apply=False,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
        use_visible=False,
        use_renderable=False,
    )


def main():
    # Blender may consume the standalone "--" before the Python script sees
    # sys.argv. Locate our option directly instead of depending on that sentinel.
    argv = sys.argv[sys.argv.index("--lod"):] if "--lod" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--lod", type=int, choices=range(4), required=True)
    args = ap.parse_args()

    target = TARGETS[args.lod]
    before = tri_count()
    after = before
    if target is not None:
        before, after = decimate_to(target)

    out = ROOT / f"assets/export/lightcycle.lod{args.lod}.glb"
    export(out)
    print(f"LOD{args.lod} OK -> {out} ({after:,} tris; source {before:,})")


main()
