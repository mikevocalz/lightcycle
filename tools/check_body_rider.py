#!/usr/bin/env python3
"""Sample fixed non-contact shell surfaces against the authoritative rider.

Checks loaded canonical geometry, or a current-source fixture without saving it.
Vertices, edge midpoints and triangle centers are samples, not a continuous
intersection proof. Intentional contact pads/controls are excluded explicitly.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_canopy_sweep as sweep

PARTS = ("LC_Body_Core", "LC_Body_Spine", "LC_Belly", "LC_Underbody", "LC_RiderMount") + tuple(
    f"LC_{part}_{side}" for part in ("Nose_Shell", "Mid_Shell", "Rear_Shell", "Armor") for side in ("L", "R")
)

def main():
    sweep.PARTS = PARTS
    loaded = Path(bpy.data.filepath) if bpy.data.filepath else None
    if loaded:
        made = {entry["name"]: bpy.data.objects[entry["name"]] for entry in sweep.builder.NODES}
        sweep.restore_rest_pose(made.values())
        bpy.context.view_layer.update()
    else:
        made = sweep.make_fixture()
    samples = sweep.surface_samples(made)
    result = {}
    for name, local in samples.items():
        matrix = np.array(made[name].matrix_world)
        points = local @ matrix[:3, :3].T + matrix[:3, 3]
        closest = {"margin_m": float("inf")}
        for limb, a, b, radius in sweep.rider_capsules():
            axis = b-a
            t = np.clip((points-a)@axis/(axis@axis), 0, 1)
            margins = np.linalg.norm(points-(a+t[:,None]*axis), axis=1)-radius
            index = int(np.argmin(margins))
            if margins[index] < closest["margin_m"]:
                closest = {"margin_m": float(margins[index]), "limb": limb, "point": points[index].tolist()}
        result[name] = closest
    failures = {name: row for name,row in result.items() if row["margin_m"] < .002}
    report = {"result": "fail" if failures else "pass", "method": "sampled rounded rider capsules; 2mm clearance",
              "source_blend": str(loaded) if loaded else None,
              "source_sha256": hashlib.sha256(loaded.read_bytes()).hexdigest() if loaded else None,
              "nodes": result, "failures": failures}
    out = sweep.ROOT / "assets/evidence/body-rider.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    if failures:
        raise RuntimeError(f"{len(failures)} non-contact shell parts intersect rider margin")
    print("BODY RIDER PASS")

if __name__ == "__main__":
    main()
