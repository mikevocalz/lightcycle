#!/usr/bin/env python3
"""Check actual canopy surfaces against the solved rider throughout animation.

  blender --factory-startup -b --python-exit-code 1 -P tools/check_canopy_sweep.py

Builds only the seven canopy meshes in memory, with lightweight placeholders for
the other contractual nodes. No canonical .blend/GLB/render outputs are written.
When invoked with Blender's -b path/to/source.blend, checks that loaded geometry
instead of creating the lightweight source fixture.
Samples evaluated vertices, triangle centroids and edge midpoints against
conservative rounded rider capsules. This is a rider-clearance regression, not a
claim of canopy-to-body self-collision or complete continuous collision checking.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_lightcycle as builder
from rest_pose import capture_rest_pose, restore_rest_pose
from rider_proxy import ANTHRO, ARM_Y, LEG_Y, solve_rider

ROOT = Path(__file__).resolve().parent.parent
PARTS = (
    "LC_Canopy_Center", "LC_Canopy_L", "LC_Canopy_R", "LC_BackSupport",
    "LC_DeployArm_L", "LC_DeployArm_R", "LC_CanopyEnergy",
)
CLIPS = {
    "LC_HighSpeedTransform": 36,
    "LC_HighSpeedReverse": 30,
    "LC_Viro_HighSpeedEnter": 36,
    "LC_Viro_HighSpeedLoop": 48,
    "LC_Viro_HighSpeedExit": 30,
}
SOURCES = (
    "tools/check_canopy_sweep.py", "tools/build_lightcycle.py",
    "tools/rest_pose.py", "tools/rider_proxy.py", "tools/geo/cockpit.py",
    "tools/geo/chassis.py", "tools/geo/_lib.py", "spec/lightcycle.spec.json",
    "spec/lightcycle.nodes.json",
)


def rider_capsules():
    contacts = builder.D["riderEnvelope"]["contactPoints"]
    joints, arm_state, leg_state = solve_rider(
        (0.02, 0.62),
        {"grip": tuple(contacts["grip"]), "peg": tuple(contacts["footPeg"])},
    )
    if arm_state != "ok" or leg_state != "ok":
        raise RuntimeError(f"Rider solve failed: {arm_state}, {leg_state}")
    limbs = []

    def add(name, a, b, radius, y=0):
        limbs.append((name, np.array([a[0], y, a[1]]),
                      np.array([b[0], y, b[1]]), radius))

    add("torso", joints["hip"], joints["shoulder"], ANTHRO["chest_depth"] / 2)
    add("head", joints["shoulder"], joints["head"], 0.115)
    for side in (-1, 1):
        suffix = "L" if side > 0 else "R"
        add("upper_arm_" + suffix, joints["shoulder"], joints["elbow"], 0.052, side * ARM_Y)
        add("forearm_" + suffix, joints["elbow"], joints["wrist"], 0.045, side * ARM_Y)
        add("thigh_" + suffix, joints["hip"], joints["knee"], 0.075, side * LEG_Y)
        add("shin_" + suffix, joints["knee"], joints["ankle"], 0.055, side * LEG_Y)
        add("foot_" + suffix, joints["ankle"], joints["ball"], 0.045, side * LEG_Y)
    return limbs


def make_fixture():
    builder.reset_scene()
    builder._ACTIONS.clear()
    made = {}
    for entry in builder.NODES:
        name = entry["name"]
        if name in PARTS:
            obj = builder.make_mesh(entry, {})
        else:
            obj = bpy.data.objects.new(name, None)
            bpy.context.scene.collection.objects.link(obj)
            obj.location = builder.production_pivot(name) or builder.EMPTY_AT.get(name, (0, 0, 0))
        obj.name = name
        made[name] = obj
    bpy.context.view_layer.update()
    for entry in builder.NODES:
        if entry["parent"]:
            obj = made[entry["name"]]
            obj.parent = made[entry["parent"]]
            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
    bpy.context.view_layer.update()
    capture_rest_pose(made.values())
    builder.author_clips(made)
    restore_rest_pose(made.values())
    bpy.context.view_layer.update()
    return made


def surface_samples(made):
    graph = bpy.context.evaluated_depsgraph_get()
    samples = {}
    for name in PARTS:
        obj = made[name].evaluated_get(graph)
        mesh = obj.to_mesh()
        mesh.calc_loop_triangles()
        vertices = np.array([list(vertex.co) for vertex in mesh.vertices])
        triangles = np.array([list(triangle.vertices) for triangle in mesh.loop_triangles])
        edges = np.array([list(edge.vertices) for edge in mesh.edges])
        samples[name] = np.concatenate((vertices, vertices[triangles].mean(axis=1), vertices[edges].mean(axis=1)))
        obj.to_mesh_clear()
    return samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--clearance-mm", type=float, default=2.0)
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        positions = [i for i, value in enumerate(sys.argv) if value in {"--out", "--clearance-mm"}]
        argv = sys.argv[min(positions):] if positions else []
    args = parser.parse_args(argv)
    if not math.isfinite(args.clearance_mm) or args.clearance_mm < 0:
        parser.error("--clearance-mm must be finite and nonnegative")
    hashes = {source: hashlib.sha256((ROOT / source).read_bytes()).hexdigest() for source in SOURCES}
    source_blend = Path(bpy.data.filepath) if bpy.data.filepath else None
    blend_hash = hashlib.sha256(source_blend.read_bytes()).hexdigest() if source_blend else None
    if source_blend:
        made = {entry["name"]: bpy.data.objects[entry["name"]] for entry in builder.NODES}
        restore_rest_pose(made.values(), require_recorded=True)
        bpy.context.view_layer.update()
    else:
        made = make_fixture()
    samples = surface_samples(made)
    limbs = rider_capsules()
    minima = {name: {"margin_m": float("inf")} for name in PARTS}
    total_frames = 0

    def inspect(clip, frame):
        nonlocal total_frames
        total_frames += 1
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        for name, local_points in samples.items():
            matrix = np.array([list(row) for row in made[name].evaluated_get(graph).matrix_world])
            points = local_points @ matrix[:3, :3].T + matrix[:3, 3]
            for limb, a, b, radius in limbs:
                axis = b - a
                t = np.clip((points - a) @ axis / (axis @ axis), 0, 1)
                margins = np.linalg.norm(points - (a + t[:, None] * axis), axis=1) - radius
                index = int(np.argmin(margins))
                if margins[index] < minima[name]["margin_m"]:
                    minima[name] = {
                        "margin_m": float(margins[index]), "limb": limb,
                        "clip": clip, "frame": frame, "point": points[index].tolist(),
                    }

    inspect("REST", 1)
    for clip, last_frame in CLIPS.items():
        restore_rest_pose(made.values())
        for obj in made.values():
            animation = obj.animation_data
            if animation is None:
                continue
            track = next((track for track in animation.nla_tracks if track.name == clip), None)
            if track:
                strip = track.strips[0]
                animation.action = strip.action
                animation.action_slot = strip.action_slot
        frames = (1, 24, 48) if clip.endswith("Loop") else range(1, last_frame + 1)
        for frame in frames:
            inspect(clip, frame)

    failures = [name for name, row in minima.items() if row["margin_m"] < args.clearance_mm / 1000]
    report = {
        "schema": "lightcycle.canopy-rider-sweep.v1", "result": "fail" if failures else "pass",
        "source_sha256": hashes, "required_clearance_mm": args.clearance_mm,
        "geometry_input": "loaded_source_blend" if source_blend else "current_source_fixture",
        "source_blend": str(source_blend) if source_blend else None,
        "source_blend_sha256": blend_hash,
        "rider_proxy": "authoritative solver, conservative capsule volumes",
        "sampled_frames": total_frames, "surface_samples": {name: len(points) for name, points in samples.items()},
        "closest_by_node": minima, "failed_nodes": failures, "shared_assets_modified": False,
        "scope": "Rider clearance only; not body self-collision or a continuous-collision proof.",
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("CANOPY SWEEP FAILED: " + ", ".join(failures))
    print("CANOPY SWEEP OK")


if __name__ == "__main__":
    main()
