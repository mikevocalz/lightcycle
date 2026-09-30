#!/usr/bin/env python3
"""Render the Light Cycle QA matrix and the lights-off material gate.

Single shot:
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/render_matrix.py -- --color gold --view reactor

Full canonical color/view matrix:
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/render_matrix.py -- --matrix --engine BLENDER_EEVEE --res 720

Silhouette gate (four orthographic views and two obliques):
  blender -b assets/source/lightcycle_blockout.blend \
    -P tools/render_matrix.py -- --clay-suite --output-dir assets/render/clay

Runtime GLB is Y-up, but this authoring .blend remains Blender-native Z-up.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from rest_pose import restore_rest_pose

SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())

VIEWS = {
    "side":     ((0.0, -5.4, 0.52), (0.0, 0, 0.52)),
    "front34":  ((-2.9, -3.3, 1.35), (0.0, 0, 0.50)),
    "rear34":   ((3.0, -3.2, 1.35), (0.1, 0, 0.52)),
    "front":    ((-4.4, 0.0, 0.52), (0.0, 0, 0.52)),
    "rear":     ((4.4, 0.0, 0.52), (0.0, 0, 0.52)),
    "top":      ((0.0, 0.0, 4.6), (0.0, 0, 0.5)),
    "reactor":  ((0.16, -1.42, 0.60), (0.30, 0, 0.42)),
    "wheel":    ((-1.62, -1.72, 0.86), (-0.96, 0, 0.46)),
    "front-wheel": ((-1.62, -1.72, 0.86), (-0.96, 0, 0.46)),
    "rear-wheel":  ((1.62, -1.72, 0.86), (0.96, 0, 0.46)),
}
ORTHOGRAPHIC_VIEWS = {"side", "front", "rear", "top"}
CLAY_VIEWS = ("side", "front", "rear", "top", "front34", "rear34")
# Keep the old `wheel` CLI name, but do not render its alias twice per matrix.
MATRIX_VIEWS = tuple(view for view in VIEWS if view != "front-wheel")

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


def evaluated_points(prefixes):
    """Measured world-space vertices, including bevels and current transforms.

    Collision proxies, the QA floor, and lights must never affect framing.
    Reading these points does not hide shell geometry in a detail capture.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    names = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render or not obj.name.startswith(prefixes):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points.extend(evaluated.matrix_world @ vertex.co for vertex in mesh.vertices)
            names.append(obj.name)
        finally:
            evaluated.to_mesh_clear()
    if not points:
        raise RuntimeError(f"No visible geometry for camera bounds: {prefixes}")
    return points, names


def bounds_center(points):
    return Vector(tuple((min(p[i] for p in points) + max(p[i] for p in points)) / 2
                        for i in range(3)))


def frame_points(cam, points, direction, margin):
    """Fit every evaluated vertex into the camera with a visible safety border."""
    center = bounds_center(points)
    direction = Vector(direction).normalized()  # from target toward camera
    # Looking exactly down the Z axis leaves track-quaternion roll ambiguous.
    # Pin plan-view +X to screen right so the bike's -X front stays on the left.
    rotation = (Quaternion((1, 0, 0, 0)) if direction.z > 0.999999
                else (-direction).to_track_quat("-Z", "Y"))
    right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
    offsets = [point - center for point in points]
    width = 2 * max(abs(point.dot(right)) for point in offsets)
    height = 2 * max(abs(point.dot(up)) for point in offsets)
    scene = bpy.context.scene
    aspect = (scene.render.resolution_x * scene.render.pixel_aspect_x
              / (scene.render.resolution_y * scene.render.pixel_aspect_y))
    if cam.data.type == "ORTHO":
        cam.data.ortho_scale = max(width, height * aspect) * margin
        distance = max(4.0, max(point.length for point in offsets) * 3)
    else:
        frame = cam.data.view_frame(scene=scene)
        tan_x = max(abs(point.x / point.z) for point in frame)
        tan_y = max(abs(point.y / point.z) for point in frame)
        distance = max(max(abs(point.dot(right)) * margin / tan_x,
                           abs(point.dot(up)) * margin / tan_y)
                       + point.dot(direction) for point in offsets)
        distance = max(distance, 0.1)
    cam.location = center + direction * distance
    cam.rotation_euler = rotation.to_euler()
    return center


def set_camera(view: str):
    loc, target = VIEWS[view]
    cam = bpy.data.objects.get("QA_Cam")
    if cam is None:
        cam_data = bpy.data.cameras.new("QA_Cam")
        cam = bpy.data.objects.new("QA_Cam", cam_data)
        bpy.context.collection.objects.link(cam)
    cam.data.type = "ORTHO" if view in ORTHOGRAPHIC_VIEWS else "PERSP"
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.clip_start, cam.data.clip_end = 0.01, 100
    cam.data.lens = 85 if view == "reactor" else (62 if "wheel" in view else 50)
    prefixes = ("LC_",)
    direction = Vector(loc) - Vector(target)
    margin = 1.12
    if view == "reactor":
        prefixes = ("LC_Reactor_", "LC_Gyro_")
        # Slightly above the side axis reveals ring depth without aiming down
        # into the upper shell. Frame the full assembly plus its body aperture.
        direction = Vector((-0.10, -1.0, 0.12))
        margin = 1.32
    elif view in {"wheel", "front-wheel", "rear-wheel"}:
        side = "Rear" if view == "rear-wheel" else "Front"
        prefixes = (f"LC_Wheel_{side}",)
        margin = 1.15
    points, names = evaluated_points(prefixes)
    center = frame_points(cam, points, direction, margin)
    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()
    return {
        "projection": cam.data.type,
        "location": list(cam.location),
        "target": list(center),
        "lens_mm": cam.data.lens if cam.data.type == "PERSP" else None,
        "ortho_scale": cam.data.ortho_scale if cam.data.type == "ORTHO" else None,
        "framed_nodes": names,
        "fit_margin": margin,
        "screen_right_world": list(cam.rotation_euler.to_matrix() @ Vector((1, 0, 0))),
        "screen_up_world": list(cam.rotation_euler.to_matrix() @ Vector((0, 1, 0))),
    }


def configure_scene(args):
    if not bpy.data.filepath:
        raise SystemExit("Load the built source first: blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- ...")
    if args.isolate and args.view == "reactor":
        raise SystemExit("Reactor QA must retain its surrounding body aperture; omit --isolate.")
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
    bpy.context.view_layer.material_override = None
    args.clay_overridden_nodes = []
    if args.clay:
        # Broad pale materials under the hero studio otherwise approach white
        # and lose the shallow surface changes this pass is intended to judge.
        s.view_settings.exposure -= 0.75
        mat = bpy.data.materials.new("QA_Clay")
        mat.use_nodes = True
        shader = mat.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = (0.24, 0.24, 0.24, 1)
        shader.inputs["Metallic"].default_value = 0.0
        shader.inputs["Roughness"].default_value = 0.68
        shader.inputs["Emission Strength"].default_value = 0.0
        # Override cycle material slots only. A scene-wide override also turns
        # the studio floor pale, erasing the top-view silhouette and contact.
        # This render process never saves the modified authoring file.
        for obj in bpy.context.scene.objects:
            if obj.type != "MESH" or obj.hide_render or not obj.name.startswith("LC_"):
                continue
            if obj.material_slots:
                for slot in obj.material_slots:
                    slot.material = mat
            else:
                obj.data.materials.append(mat)
            args.clay_overridden_nodes.append(obj.name)
        floor_shader = bpy.data.objects["QA_Floor"].data.materials[0].node_tree.nodes["Principled BSDF"]
        floor_shader.inputs["Base Color"].default_value = (0.012, 0.012, 0.012, 1)
        floor_shader.inputs["Roughness"].default_value = 0.82


def render_one(view, color, lights_off, args, out=None):
    lights_off = lights_off or args.clay
    set_energy(None if lights_off else color, lights_off)
    camera = set_camera(view)
    tag = "clay" if args.clay else ("lightsoff" if lights_off else color)
    if args.isolate:
        tag += "_iso"
    path = Path(out) if out else (
        Path(args.output_dir) / f"{view}_{tag}.png"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    evidence = {
        "schema": "lightcycle.render-evidence.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_blend": str(Path(bpy.data.filepath).resolve()),
        "source_sha256": args.source_sha256,
        "renderer_sha256": args.renderer_sha256,
        "rest_pose": args.rest_pose,
        "freshness": "Capture of the loaded blend; source hash does not prove it was rebuilt from current geometry code.",
        "image": str(path.resolve()),
        "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "view": view,
        "context": args.context,
        "color": None if lights_off else color,
        "clay": args.clay,
        "clay_override_scope": "visible_cycle_mesh_material_slots" if args.clay else None,
        "clay_overridden_nodes": args.clay_overridden_nodes,
        "lights_off": lights_off,
        "isolate": args.isolate,
        "engine": args.engine,
        "exposure": bpy.context.scene.view_settings.exposure,
        "resolution": [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
        "camera": camera,
        "human_visual_approval": False,
    }
    path.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
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
    ap.add_argument("--clay", action="store_true", help="Neutral material override with all energy disabled")
    ap.add_argument("--clay-suite", action="store_true", help="Six silhouette views: four true orthographics and two obliques")
    ap.add_argument("--color", default="blue", choices=list(SPEC["colors"]))
    ap.add_argument("--view", default="front34", choices=list(VIEWS))
    ap.add_argument("--engine", default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--res", type=int, default=1280)
    ap.add_argument("--out", default=None)
    ap.add_argument("--output-dir", default=None, help="Directory for images and per-image evidence JSON")
    ap.add_argument("--isolate", default=None)
    ap.add_argument("--context", default="dark", choices=list(CONTEXTS))
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--matrix-colors", default=",".join(SPEC["colors"].keys()))
    ap.add_argument("--matrix-views", default=",".join(MATRIX_VIEWS))
    args = ap.parse_args(argv)
    args.clay = args.clay or args.clay_suite
    args.output_dir = args.output_dir or str(ROOT / "assets/render" / args.context)
    if args.out and (args.matrix or args.clay_suite):
        ap.error("--out is for one image; use --output-dir for a suite")
    if args.isolate and (args.matrix or args.clay_suite):
        ap.error("Suites must retain the complete model; omit --isolate")
    if not bpy.data.filepath:
        ap.error("Load the built source with blender -b assets/source/lightcycle_blockout.blend")
    args.source_sha256 = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    args.renderer_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    # Authoring clips are stored in NLA tracks. Their saved evaluation must not
    # distort the silhouette camera or masquerade as a modeled body defect.
    # Missing metadata means this blend predates the reproducible rest contract.
    try:
        asset_objects = [obj for obj in bpy.context.scene.objects
                         if obj.name.startswith(("LC_", "COL_"))]
        args.rest_pose = restore_rest_pose(asset_objects, require_recorded=True)
        bpy.context.view_layer.update()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"Cannot capture authoritative rest pose: {error}. Rebuild with npm run build:glb first.") from error
    configure_scene(args)

    if args.clay_suite:
        for view in CLAY_VIEWS:
            render_one(view, args.color, True, args)
        print(f"CLAY SUITE OK -> {len(CLAY_VIEWS)} renders")
        return

    if not args.matrix:
        render_one(args.view, args.color, args.lights_off, args, args.out)
        return

    colors = csv_arg(args.matrix_colors, SPEC["colors"])
    views = csv_arg(args.matrix_views, VIEWS)
    if args.clay:
        for view in views:
            render_one(view, args.color, True, args)
        print(f"CLAY MATRIX OK -> {len(views)} renders")
        return
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
