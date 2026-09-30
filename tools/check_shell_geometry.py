#!/usr/bin/env python3
"""Measure new fixed shell vertices against protected mechanical envelopes.

Run in Blender against the rebuilt source. This sampled geometric guard is not
a full swept-volume/BVH collision proof or a human visual acceptance check.
"""
import hashlib
import json
import sys
import math
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())["dimensions_m"]
NAMES = ["LC_Body_Core", "LC_Body_Spine", "LC_Belly", "LC_Underbody",
         "LC_RiderMount", "LC_Canopy_Center", "LC_Canopy_L", "LC_Canopy_R", "LC_BackSupport"] + [
    f"LC_{part}_{side}"
    for part in ("Nose_Shell", "Mid_Shell", "Rear_Shell", "Armor")
    for side in ("L", "R")
]


def main():
    sys.path.insert(0,str(ROOT / "tools"))
    from rest_pose import restore_rest_pose
    objects=[o for o in bpy.context.scene.objects if o.name.startswith(("LC_","COL_"))]
    restore_rest_pose(objects, require_recorded=True)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    failures = []
    result = {}
    for name in NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            failures.append(f"missing shell {name}")
            continue
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        bounds = [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]
        tire_hits = 0
        tire_points = []
        reactor_hits = 0
        for p in points:
            # Only points inside the tire's lateral slab can collide with its
            # radial envelope. A fairing outside that slab may embrace its side.
            if abs(p.y) < D["wheelSectionWidth"] / 2 + .003:
                for sign in (-1, 1):
                    radius = math.hypot(p.x - sign * D["wheelbase"] / 2, p.z - D["wheelOuterDiameter"] / 2)
                    if D["hubVoidDiameter"] / 2 < radius < D["wheelOuterDiameter"] / 2 + .003:
                        tire_hits += 1
                        if len(tire_points) < 5:
                            tire_points.append(list(p))
            # Reactor has nested rings/gyros. Keep fixed chassis out of its
            # conservative central swept envelope, including the hidden core.
            if abs(p.y) < .155 and math.hypot(p.x - .30, p.z - .40) < .208:
                reactor_hits += 1
        evaluated.to_mesh_clear()
        result[name] = {"bounds": bounds, "vertices": len(points), "tireEnvelopeHits": tire_hits, "tireExamples": tire_points, "reactorEnvelopeHits": reactor_hits}
        if tire_hits or reactor_hits:
            failures.append(f"{name}: tire={tire_hits}, reactor={reactor_hits}")
        if bounds[2][0] < D["groundClearance"] - .001:
            failures.append(f"{name}: below ground clearance {bounds[2][0]:.4f}")
    report = {"source": bpy.data.filepath,
              "sourceSha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
              "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "method": "evaluated shell vertex envelope sampling", "parts": result, "failures": failures}
    out = ROOT / "assets/evidence/shell-geometry.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    for failure in failures:
        print("SHELL GEOMETRY FAIL:", failure)
    if failures:
        raise RuntimeError(f"{len(failures)} shell envelope checks failed; see {out}")
    print(f"SHELL GEOMETRY OK: {len(result)} parts; sampled tire/reactor/ground clearance")


main()
