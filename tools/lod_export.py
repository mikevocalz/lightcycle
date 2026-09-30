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
    0: 300_000,
    1: 150_000,
    2: 70_000,
    3: 30_000,
}


def apply_render_modifiers():
    """Bake the source bevel stack before LOD measurement/decimation.

    LOD budgets must describe what ships, not the pre-bevel control cage.
    Collision proxies remain untouched and are hidden from render export.
    """
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.name.startswith("COL_"):
            continue
        if not o.modifiers:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        o.select_set(False)


def tri_count():
    total = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.name.startswith("COL_"):
            continue
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def decimate_to(target: int):
    """Collapse large render meshes until the final baked geometry fits target.

    One global ratio is not exact because small/emissive parts are protected and
    Blender rounds per-mesh collapses independently. Use bounded corrective
    passes instead of pretending a requested ratio is the shipped triangle count.
    """
    source = tri_count()
    current = source
    for pass_index in range(3):
        if current <= target:
            break

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
        # Aim a little below target to absorb per-object integer rounding.
        ratio = max(0.025, min(0.995, wanted_variable / max(1, variable) * 0.975))
        if ratio >= 0.995 or not candidates:
            break

        for o, _tris in candidates:
            m = o.modifiers.new(f"__LC_LOD_DECIMATE_{pass_index}__", "DECIMATE")
            m.decimate_type = "COLLAPSE"
            m.ratio = ratio
            if hasattr(m, "use_collapse_triangulate"):
                m.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.modifier_apply(modifier=m.name)
            o.select_set(False)

        next_count = tri_count()
        print(f"LOD pass {pass_index + 1}: {current:,} -> {next_count:,} tris "
              f"(ratio {ratio:.4f}, target <= {target:,})")
        if next_count >= current:
            break
        current = next_count

    if current > target:
        raise RuntimeError(f"LOD decimation missed target: {current:,} > {target:,}")
    return source, current


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
    args = ap.parse_args(argv)

    apply_render_modifiers()
    target = TARGETS[args.lod]
    before = tri_count()
    after = before
    if target is not None:
        before, after = decimate_to(target)

    out = ROOT / f"assets/export/lightcycle.lod{args.lod}.glb"
    export(out)
    print(f"LOD{args.lod} OK -> {out} ({after:,} tris; source {before:,})")


main()
