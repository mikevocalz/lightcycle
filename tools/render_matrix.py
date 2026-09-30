#!/usr/bin/env python3
"""Render the QA matrix, including the lights-off material-validation shot.

    blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --lights-off
    blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --color gold --view side

--lights-off zeroes every emissive channel. That shot is doc 18's quality gate:
if the machine stops looking expensive once the glow is gone, the fix belongs in
the geometry and the material library, never in the bloom.

Engine strings valid in Blender 5.2.1 are BLENDER_EEVEE, BLENDER_WORKBENCH and
CYCLES. BLENDER_EEVEE_NEXT does not exist in this build.
"""
import argparse, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())

VIEWS = {  # (camera location, look-at) in metres
    "side":     ((0.0, -5.4, 0.78), (0.0, 0, 0.52)),
    "front34":  ((-2.9, -3.3, 1.35), (0.0, 0, 0.50)),
    "rear34":   ((3.0, -3.2, 1.35), (0.1, 0, 0.52)),
    "front":    ((-4.4, 0.0, 0.85), (0.0, 0, 0.52)),
    "top":      ((0.0, 0.0, 4.6), (0.0, 0, 0.5)),
    "reactor":  ((0.05, -1.05, 0.62), (0.30, 0, 0.46)),
    "wheel":    ((-1.35, -1.25, 0.70), (-0.96, 0, 0.46)),
}


def srgb_to_linear(h):
    h = h.lstrip("#")
    return tuple((c / 12.92 if (c := int(h[i:i+2], 16) / 255) <= 0.04045
                  else ((c + 0.055) / 1.055) ** 2.4) for i in (0, 2, 4))


def set_energy(color: str | None, lights_off: bool):
    """Drive the emissive library the way the runtime adapters do."""
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


def studio(lights_off: bool):
    """Dark grid, hard key, cool rim. Tuned so a mirror-metal part is still readable
    without emissives - that readability is the thing the gate is judging."""
    world = bpy.data.worlds.new("LC_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.016, 0.019, 0.024, 1)
    bg.inputs[1].default_value = 1.0 if lights_off else 0.45

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

    # Wet grid floor - gives the metals something to reflect, which is most of
    # what makes a hard-surface asset read as expensive with the lights off.
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "QA_Floor"
    fm = bpy.data.materials.new("QA_Floor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0.006, 0.007, 0.009, 1)
    fb.inputs["Roughness"].default_value = 0.14
    floor.data.materials.append(fm)


def camera(view: str):
    loc, target = VIEWS[view]
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.lens = 85 if view in ("reactor", "wheel") else 50
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam


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
    a = ap.parse_args(argv)

    for o in list(bpy.data.objects):
        if o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)

    set_energy(None if a.lights_off else a.color, a.lights_off)
    studio(a.lights_off)
    camera(a.view)

    s = bpy.context.scene
    s.render.engine = a.engine
    s.render.resolution_x, s.render.resolution_y = a.res, int(a.res * 9 / 16)
    s.render.film_transparent = False
    if a.engine == "CYCLES":
        s.cycles.samples = a.samples
        s.cycles.device = "CPU"
        s.cycles.use_denoising = True
    # AgX holds hue through the highlight rolloff; Filmic/Standard wash the
    # saturated energy colours out, which is the failure doc 17 screens for.
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Base Contrast"

    tag = "lightsoff" if a.lights_off else a.color
    out = a.out or str(ROOT / f"assets/render/{a.view}_{tag}.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    s.render.filepath = out
    s.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"RENDER OK -> {out}")


main()
