#!/usr/bin/env python3
"""Blender regression: rest pose survives the clip library, save/reload and export.

  blender --factory-startup -b --python-exit-code 1 -P tools/check_rest_pose.py

Uses lightweight named objects plus the real steering yoke. Outputs go to a
temporary directory; no shared production asset is built or replaced.
"""
import json
import struct
import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_lightcycle as builder
from rest_pose import capture_rest_pose, restore_rest_pose
from validate_glb import read_glb_json


def matrix_values(matrix):
    return [value for row in matrix for value in row]


def assert_rest(expected):
    bpy.context.view_layer.update()
    for name, values in expected.items():
        obj = bpy.data.objects[name]
        actual = matrix_values(obj.matrix_basis)
        assert max(abs(a - b) for a, b in zip(actual, values)) < 1e-6, f"{name}: rest transform changed"
        if obj.animation_data:
            assert not obj.animation_data.use_nla, f"{name}: simultaneous NLA playback is enabled"
            assert all(not strip.mute for track in obj.animation_data.nla_tracks for strip in track.strips)


def animation_samples(gltf, binary, clip_name, node_name, path):
    """Read the actual exported channel, not the Blender source keyframes."""
    animation = next(item for item in gltf["animations"] if item["name"] == clip_name)
    node_index = next(i for i, node in enumerate(gltf["nodes"]) if node.get("name") == node_name)
    channel = next(item for item in animation["channels"]
                   if item["target"] == {"node": node_index, "path": path})
    sampler = animation["samplers"][channel["sampler"]]
    accessor = gltf["accessors"][sampler["output"]]
    assert accessor["componentType"] == 5126, "animation output must use floats"
    width = {"VEC3": 3, "VEC4": 4}[accessor["type"]]
    view = gltf["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", width * 4)
    samples = [struct.unpack_from("<" + "f" * width, binary, start + i * stride)
               for i in range(accessor["count"])]
    # Cubic spline outputs interleave incoming tangent, value, outgoing tangent.
    return samples[1::3] if sampler.get("interpolation") == "CUBICSPLINE" else samples


def assert_transition_continuity(gltf, output):
    data = output.read_bytes()
    offset = 12
    binary = None
    while offset + 8 <= len(data):
        length, kind = struct.unpack_from("<I4s", data, offset)
        if kind == b"BIN\x00":
            binary = data[offset + 8:offset + 8 + length]
            break
        offset += 8 + length
    assert binary is not None

    def matches(a, b, path):
        if path == "rotation":
            # q and -q represent the same orientation.
            return abs(abs(sum(x * y for x, y in zip(a, b))) - 1) < 1e-5
        return max(abs(x - y) for x, y in zip(a, b)) < 1e-6

    for node, path in (
        ("LC_Canopy_L", "rotation"), ("LC_Canopy_R", "rotation"),
        ("LC_DeployArm_L", "rotation"), ("LC_DeployArm_R", "rotation"),
        ("LC_RearCanopy", "translation"),
    ):
        enter = animation_samples(gltf, binary, "LC_Viro_HighSpeedEnter", node, path)
        loop = animation_samples(gltf, binary, "LC_Viro_HighSpeedLoop", node, path)
        exit_ = animation_samples(gltf, binary, "LC_Viro_HighSpeedExit", node, path)
        assert not matches(enter[0], enter[-1], path), f"{node}: high-speed motion disappeared"
        assert matches(enter[-1], loop[0], path), f"{node}: enter/loop pose mismatch"
        assert matches(loop[-1], exit_[0], path), f"{node}: loop/exit pose mismatch"
        assert matches(exit_[-1], enter[0], path), f"{node}: exit does not return to rest"
        portable_enter = animation_samples(gltf, binary, "LC_HighSpeedTransform", node, path)
        portable_exit = animation_samples(gltf, binary, "LC_HighSpeedReverse", node, path)
        assert matches(portable_enter[0], enter[0], path), f"{node}: portable/Viro rest mismatch"
        assert matches(portable_enter[-1], enter[-1], path), f"{node}: portable/Viro closed mismatch"
        assert matches(portable_exit[0], exit_[0], path), f"{node}: portable/Viro exit start mismatch"
        assert matches(portable_exit[-1], exit_[-1], path), f"{node}: portable/Viro exit end mismatch"


def main():
    builder.reset_scene()
    builder._ACTIONS.clear()
    made = {}
    for entry in builder.NODES:
        name = entry["name"]
        if name == "LC_SteeringYoke":
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

    yoke = made["LC_SteeringYoke"]
    pivot = (-builder.HALF_WB, 0, builder.AXLE_Z + builder.HUB_R + 0.09)
    assert max(abs(a - b) for a, b in zip(yoke.matrix_world.translation, pivot)) < 1e-6
    expected = {name: matrix_values(obj.matrix_basis) for name, obj in made.items()}
    try:
        restore_rest_pose(made.values())
    except RuntimeError as error:
        assert "Rest pose metadata missing" in str(error)
    else:
        raise AssertionError("stale sources without rest records were silently accepted")
    capture_rest_pose(made.values())
    builder.author_clips(made)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    assert abs(yoke.rotation_euler.z) > 0.1, "fixture did not reproduce overlapping steer clips"
    assert abs(made["LC_Canopy_L"].rotation_euler.x) > 0.1, "fixture did not reproduce displaced canopy"

    receipt = restore_rest_pose(made.values())
    assert receipt["restored_count"] == len(builder.NODES)
    bpy.context.scene.frame_set(17)
    assert_rest(expected)

    with tempfile.TemporaryDirectory(prefix="lightcycle-rest-") as directory:
        source = Path(directory) / "rest-test.blend"
        output = Path(directory) / "rest-test.glb"
        bpy.ops.wm.save_as_mainfile(filepath=str(source))
        builder.export(output)
        gltf = read_glb_json(output)
        expected_clips = set(builder.SPEC["clips"] + builder.SPEC["viroCompositeClips"])
        actual_clips = [clip["name"] for clip in gltf.get("animations", [])]
        assert len(actual_clips) == 33 and set(actual_clips) == expected_clips, actual_clips
        exported_yoke = next(node for node in gltf["nodes"] if node.get("name") == "LC_SteeringYoke")
        rotation = exported_yoke.get("rotation", [0, 0, 0, 1])
        assert max(abs(value) for value in rotation[:3]) < 1e-6, "exported yoke is not at rest"
        assert_transition_continuity(gltf, output)
        bpy.ops.wm.open_mainfile(filepath=str(source))
        restore_rest_pose(bpy.context.scene.objects)
        bpy.context.scene.frame_set(1)
        assert_rest(expected)

    print(json.dumps({
        "check": "rest_pose_and_animation_export",
        "result": "pass",
        "restored_nodes": len(expected),
        "exported_clips": len(actual_clips),
        "canopy_transition_nodes_verified": 5,
        "yoke_pivot": pivot,
        "shared_assets_modified": False,
    }))


if __name__ == "__main__":
    main()
