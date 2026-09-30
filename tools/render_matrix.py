#!/usr/bin/env python3
"""Render the Light Cycle QA matrix and the lights-off material gate.

Single shot:
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/render_matrix.py -- --color gold --view reactor

Full canonical color/view matrix:
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/render_matrix.py -- --matrix --engine BLENDER_EEVEE --res 720

Runtime GLB is Y-up, but this authoring .blend remains Blender-native Z-up.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())

VIEWS = {
    "side":     ((0.0, -5.4, 0.78), (0.0, 0, 0.52)),
    "front34":  ((-2.9, -3.3, 1.35), (0.0, 0, 0.50)),
    "rear34":   ((3.0, -3.2, 1.35), (0.1, 0, 0.52)),
    "front":    ((-4.4, 0.0, 0.85), (0.0, 0, 0.52)),
    "rear":     ((4.4, 0.0, 0.85), (0.0, 0, 0.52)),
    "top":      ((0.0, 0.0, 4.6), (0.0, 0, 0.5)),
    "reactor":  ((0.16, -1.42, 0.60), (0.30, 0, 0.42)),
    "wheel":    ((-1.62, -1.72, 0.86), (-0.96, 0, 0.46)),
}

CONTEXTS = {
    "dark": {"world": (0.016, 0.019, 0.024, 1), "strength": 0.45, "exposure": 0.0, "floor": (0.006, 0.007, 0.009, 1), "rough": 0.14},
    "bright": {"world": (0.11, 0.13, 0.16, 1), "strength": 1.15, "exposure": 0.0, "floor": (0.025, 0.030, 0.038, 1), "rough": 0.22},
    "low": {"world": (0.016, 0.019, 0.024, 1), "strength": 0.45, "exposure": -1.25, "floor": (0.006, 0.007, 0.009, 1), "rough": 0.14},
    "high": {"world": (0.016, 0.019, 0.024, 1), "strength": 0.45, "exposure": 1.25, "floor": (0.006, 0.007, 0.009, 1), "rough": 0.14},
    # Lighting-only approximation for authoring QA. It is explicitly not
    # evidence of a real headset camera/passthrough environment.
    "mr-simulated": {"world": (0.32, 0.35, 0.39, 1), "strength": 1.35, "exposure": 0.0, "floor": (0.15, 0.16, 0.17, 1), "rough": 0.55},
}


def srgb_to_linear(h):
    h = h.lstrip("#")
    return tuple(
        (c / 12.92 if (c := int(h[i:i + 2], 16) / 255) <= 0.04045
         else ((c + 0.055) / 1.055) ** 2.4)
        for i in (0, 2, 4)
    )


def set_energy(color: str | None, lights_off: bool):
    for name, m in SPEC["materials"].items():
        if not m.get("emissive"):
            continue
        mat = bpy.data.materials.get(name)
        if not mat:
            continue
        b = mat.node_tree.nodes["Principled BSDF"]
        if lights_off:
            b.inputs["Emission Strength"].default_value = 0.0
            continue
        ch = m["channel"]
        key = "core" if ch == "core" else "energy"
        b.inputs["Emission Color"].default_value = (*srgb_to_linear(SPEC["colors"][color][key]), 1)
        b.inputs["Emission Strength"].default_value = m["emissionStrength"]


def studio(context: str):
    cfg = CONTEXTS[context]
    world = bpy.data.worlds.get("LC_World") or bpy.data.worlds.new("LC_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = cfg["world"]
    bg.inputs[1].default_value = cfg["strength"]

    for nm, loc, rot, size, energy, color in [
        ("KEY",  (-2.2, -2.8, 3.2), (0.72, 0, -0.62), 3.2, 900, (1.0, 0.97, 0.93)),
        ("FILL", (3.0, -2.2, 1.4), (1.25, 0, 2.30), 2.6, 220, (0.80, 0.86, 1.0)),
        ("RIM",  (1.6, 3.4, 2.0), (1.05, 0, 3.55), 3.0, 700, (0.72, 0.84, 1.0)),
        ("KICK", (-3.2, 1.8, 0.5), (1.45, 0, -2.1), 2.0, 260, (0.90, 0.93, 1.0)),
    ]:
        d = bpy.data.lights.new(nm, "AREA")
        d.size, d.energy, d.color = size, energy, color
        o = bpy.data.objects.new(nm, d)
        o.location, o.rotation_euler = loc, rot
        bpy.context.collection.objects.link(o)

    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "QA_Floor"
    fm = bpy.data.materials.new("QA_Floor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = cfg["floor"]
    fb.inputs["Roughness"].default_value = cfg["rough"]
    floor.data.materials.append(fm)


def set_camera(view: str):
    loc, target = VIEWS[view]
    cam = bpy.data.objects.get("QA_Cam")
    if cam is None:
        cam_data = bpy.data.cameras.new("QA_Cam")
        cam = bpy.data.objects.new("QA_Cam", cam_data)
        bpy.context.collection.objects.link(cam)
    cam.data.lens = 85 if view == "reactor" else (62 if view == "wheel" else 50)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam


def configure_scene(args):
    for o in list(bpy.data.objects):
        if o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)

    if args.isolate:
        for o in bpy.data.objects:
            if o.type == "MESH" and not o.name.startswith(args.isolate):
                o.hide_render = True

    studio(args.context)
    s = bpy.context.scene
    s.render.engine = args.engine
    s.render.resolution_x = args.res
    s.render.resolution_y = int(args.res * 9 / 16)
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    if args.engine == "CYCLES":
        s.cycles.samples = args.samples
        s.cycles.device = "CPU"
        s.cycles.use_denoising = True
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Base Contrast"
    s.view_settings.exposure = CONTEXTS[args.context]["exposure"]


def render_one(view, color, lights_off, args, out=None):
    set_energy(None if lights_off else color, lights_off)
    set_camera(view)
    tag = "lightsoff" if lights_off else color
    if args.isolate:
        tag += "_iso"
    path = Path(out) if out else (
        ROOT / "assets/render" / args.context / f"{view}_{tag}.png"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"RENDER OK -> {path}")


def csv_arg(value: str, allowed):
    items = [v.strip() for v in value.split(",") if v.strip()]
    bad = [v for v in items if v not in allowed]
    if bad:
        raise SystemExit(f"invalid values {bad}; allowed: {list(allowed)}")
    return items


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--lights-off", action="store_true")
    ap.add_argument("--color", default="blue", choices=list(SPEC["colors"]))
    ap.add_argument("--view", default="front34", choices=list(VIEWS))
    ap.add_argument("--engine", default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--res", type=int, default=1280)
    ap.add_argument("--out", default=None)
    ap.add_argument("--isolate", default=None)
    ap.add_argument("--context", default="dark", choices=list(CONTEXTS))
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--matrix-colors", default=",".join(SPEC["colors"].keys()))
    ap.add_argument("--matrix-views", default=",".join(VIEWS.keys()))
    args = ap.parse_args(argv)

    configure_scene(args)

    if not args.matrix:
        render_one(args.view, args.color, args.lights_off, args, args.out)
        return

    colors = csv_arg(args.matrix_colors, SPEC["colors"])
    views = csv_arg(args.matrix_views, VIEWS)
    for color in colors:
        for view in views:
            render_one(view, color, False, args)
    # Lights-off appearance is independent of player hue, so one capture per
    # view is sufficient and avoids six byte-identical validation renders.
    for view in views:
        render_one(view, colors[0], True, args)

    total = len(colors) * len(views) + len(views)
    print(f"QA MATRIX OK -> {total} renders ({args.context})")


main()
