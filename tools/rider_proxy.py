#!/usr/bin/env python3
"""Anthropometric rider proxy + ergonomics check. Doc section 15.

    blender -b assets/source/lightcycle_blockout.blend -P tools/rider_proxy.py
    blender -b assets/source/lightcycle_blockout.blend -P tools/rider_proxy.py -- --save

The bike's contact points were placed by eye. This puts a real prone rider on it
at published segment lengths, solves the limbs forward from the hip, and reports
where the hands, knees and feet ACTUALLY land. The machine moves to meet the
rider, not the reverse - a rider who cannot reach the bars is the single fastest
way to make an expensive model look wrong.

The rider is never exported; it exists to measure against.
"""
import argparse, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())

# 50th-percentile adult male, 1.75 m, in metres. Link lengths are joint-to-joint.
ANTHRO = {
    "torso": 0.52,        # hip joint -> shoulder joint
    "neck_head": 0.30,    # shoulder -> front of helmet
    "upper_arm": 0.33,
    "forearm": 0.27,
    "hand": 0.09,         # wrist -> centre of grip
    "thigh": 0.43,
    "shin": 0.42,
    "foot": 0.11,         # ankle -> ball of foot, the part that rests on the peg
    "shoulder_breadth": 0.45,
    "hip_breadth": 0.35,
    "chest_depth": 0.24,
}


def ik2(root, target, a, b, bend=+1):
    """Two-link IK in the XZ plane. Returns (joint, reach_state).

    reach_state is 'ok', 'OUT OF REACH' when the target is further than a+b, or
    'TOO CLOSE' when it is inside |a-b|. Asking whether a real rider can reach a
    control beats picking joint angles and hoping - the bike is what moves.
    """
    (rx, rz), (tx, tz) = root, target
    dx, dz = tx - rx, tz - rz
    d = math.hypot(dx, dz)
    if d > a + b:
        return None, f"OUT OF REACH by {d - (a + b):.3f} m"
    if d < abs(a - b):
        return None, f"TOO CLOSE by {abs(a - b) - d:.3f} m"
    # Cosine rule for the elbow/knee, offset perpendicular to the root-target line.
    cos_t = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    base = math.atan2(dz, dx)
    ang = base + bend * math.acos(cos_t)
    return (rx + a * math.cos(ang), rz + a * math.sin(ang)), "ok"


def solve_rider(hip, targets):
    """Prone tuck solved to the bike's actual contact points.

    Shoulder is placed one torso-length forward of the hip along the line to the
    grips, which is what a rider does: the torso orients toward the bars.
    """
    a = ANTHRO
    gx, gz = targets["grip"]
    # Torso aims at the grips but stops one torso-length short.
    d = math.hypot(gx - hip[0], gz - hip[1]) or 1.0
    shoulder = (hip[0] + a["torso"] * (gx - hip[0]) / d,
                hip[1] + a["torso"] * (gz - hip[1]) / d)
    head = (shoulder[0] - a["neck_head"] * 0.94, shoulder[1] - a["neck_head"] * 0.22)

    # Arms: elbow bends outward/up, wrist sits one hand-length behind the grip.
    wrist = (gx + a["hand"], gz)
    elbow, arm_state = ik2(shoulder, wrist, a["upper_arm"], a["forearm"], bend=+1)
    # Legs: knee bends up, ankle sits one foot-length ahead of the peg.
    peg = targets["peg"]
    ankle = (peg[0] - a["foot"], peg[1])
    knee, leg_state = ik2(hip, ankle, a["thigh"], a["shin"], bend=+1)

    return {"hip": hip, "shoulder": shoulder, "head": head,
            "elbow": elbow, "wrist": wrist, "grip": (gx, gz),
            "knee": knee, "ankle": ankle, "ball": peg}, arm_state, leg_state


ARM_Y = ANTHRO["shoulder_breadth"] / 2 * 0.8
# Legs splay outboard of the hips so the shin clears the rear wheel: the wheel is
# 0.30 m wide, so a shin centreline at hip width would pass through it.
LEG_Y = 0.21


def limb(name, a, b, radius, y=0.0):
    """A capsule between two XZ points, mirrored to ±y when y is non-zero."""
    (x1, z1), (x2, z2) = a, b
    dx, dz = x2 - x1, z2 - z1
    length = math.hypot(dx, dz)
    for side in ((1, -1) if y else (0,)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16, radius=radius, depth=length,
            location=((x1 + x2) / 2, side * y, (z1 + z2) / 2),
            rotation=(0, math.atan2(dx, dz), 0))
        bpy.context.object.name = f"RIDER_{name}{'_L' if side == 1 else '_R' if side else ''}"


def build_rider(j):
    a = ANTHRO
    limb("Torso", j["hip"], j["shoulder"], a["chest_depth"] / 2)
    limb("Head", j["shoulder"], j["head"], 0.115)
    if j["elbow"]:
        limb("UpperArm", j["shoulder"], j["elbow"], 0.052, y=ARM_Y)
        limb("Forearm", j["elbow"], j["wrist"], 0.045, y=ARM_Y)
    if j["knee"]:
        limb("Thigh", j["hip"], j["knee"], 0.075, y=LEG_Y)
        limb("Shin", j["knee"], j["ankle"], 0.055, y=LEG_Y)
        limb("Foot", j["ankle"], j["ball"], 0.045, y=LEG_Y)


def xz(name):
    """World-space geometry centre, not the object origin.

    Production bmeshes are authored in world space and several objects keep an
    origin chosen for animation rather than for measurement. The bounding-box
    centre is therefore the correct ergonomics probe.
    """
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    if o.type == "MESH" and o.data.vertices:
        corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return (
            sum(p.x for p in corners) / len(corners),
            sum(p.z for p in corners) / len(corners),
        )
    p = o.matrix_world.translation
    return (p.x, p.z)


def wheel_clear(j):
    """Feet and shins must pass OUTBOARD of the rear wheel, not through it.
    Side-view clearance alone is not enough - the wheel has real width."""
    D = SPEC["dimensions_m"]
    cx, cz, r = D["wheelbase"] / 2, D["wheelOuterDiameter"] / 2, D["wheelOuterDiameter"] / 2
    half_w = D["wheelSectionWidth"] / 2
    out = []
    for label, (px, pz) in (("foot", j["ball"]), ("ankle", j["ankle"])):
        inside = math.hypot(px - cx, pz - cz) < r
        lateral_ok = LEG_Y > half_w
        out.append((label, inside, lateral_ok,
                    "ok" if not inside else
                    ("ok (passes outboard)" if lateral_ok else "THROUGH REAR WHEEL")))
    return out


def report(j, arm_state, leg_state):
    """Compare where the rider's contact points land against where the bike put them."""
    print("\n--- ERGONOMICS (doc section 15) ---")
    print(f"arm reach to grips : {arm_state}")
    print(f"leg reach to pegs  : {leg_state}")
    if not j["elbow"] or not j["knee"]:
        print("\nunreachable contact point - move the part, the rider is fixed")
        return ["unreachable"]

    checks = [
        ("hands -> handlebars", j["grip"], "LC_Handlebar_L", 0.06),
        ("chest -> chest support", ((j["hip"][0] + j["shoulder"][0]) / 2,
                                    (j["hip"][1] + j["shoulder"][1]) / 2 - ANTHRO["chest_depth"] / 2),
         "LC_ChestSupport", 0.07),
        ("knee -> shin rest", j["knee"], "LC_ShinRest_L", 0.09),
        ("feet -> foot rest", j["ball"], "LC_FootRest_L", 0.06),
    ]
    print(f"\n{'contact':24} {'rider lands at':>18} {'bike part at':>18} {'dx':>7} {'dz':>7}  verdict")
    fails = []
    for label, (rx, rz), part, tol in checks:
        pt = xz(part)
        if pt is None:
            print(f"{label:24} {'MISSING ' + part:>18}")
            continue
        dx, dz = rx - pt[0], rz - pt[1]
        ok = math.hypot(dx, dz) <= tol
        print(f"{label:24} ({rx:6.3f},{rz:6.3f}) ({pt[0]:6.3f},{pt[1]:6.3f}) {dx:7.3f} {dz:7.3f}  "
              f"{'ok' if ok else 'MOVE PART'}")
        if not ok:
            fails.append((part, rx, rz))

    print()
    for label, inside, lateral, verdict in wheel_clear(j):
        print(f"{label + ' vs rear wheel':24} {'intersects in side view' if inside else 'clear':>37}  {verdict}")
        if inside and not lateral:
            fails.append(("REAR WHEEL CLEARANCE", 0, 0))

    D = SPEC["dimensions_m"]
    top = max(j["shoulder"][1] + ANTHRO["chest_depth"] / 2,
              (j["knee"][1] if j["knee"] else 0) + 0.075)
    front, back = j["head"][0] - 0.10, j["ball"][0] + 0.05
    print(f"\nrider occupies x [{front:.3f} .. {back:.3f}] = {back - front:.3f} m, tops out at z {top:.3f} m")
    canopy = xz("LC_Canopy_Center")
    if canopy:
        clears = canopy[1] > top
        print(f"canopy centre z {canopy[1]:.3f} vs rider top {top:.3f} -> "
              f"{'CLEARS' if clears else 'INTERSECTS RIDER'}")
        if not clears:
            fails.append(("LC_Canopy_Center", canopy[0], top + 0.06))
    need_h = top + 0.06
    print(f"height: rider needs {need_h:.3f} m, spec says {D['height']:.3f} m -> "
          f"{'ok' if D['height'] >= need_h else 'RAISE dimensions_m.height to ' + f'{need_h:.3f}'}")

    if fails:
        print("\nmove these (x, z):")
        for part, rx, rz in fails:
            print(f"  {part}: x={rx:.3f}  z={rz:.3f}")
    else:
        print("\nALL ERGONOMICS CHECKS PASS")
    return fails


def main():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        custom = {"--hip-x", "--hip-z", "--grip", "--peg", "--save"}
        positions = [i for i, value in enumerate(sys.argv) if value in custom]
        argv = sys.argv[min(positions):] if positions else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--hip-x", type=float, default=0.02)
    ap.add_argument("--hip-z", type=float, default=0.62)
    ap.add_argument("--grip", type=float, nargs=2, default=[-0.72, 0.70])
    ap.add_argument("--peg", type=float, nargs=2, default=[0.62, 0.28])
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args(argv)

    j, arm_state, leg_state = solve_rider((a.hip_x, a.hip_z),
                                          {"grip": tuple(a.grip), "peg": tuple(a.peg)})
    build_rider(j)
    fails = report(j, arm_state, leg_state)
    if a.save:
        out = ROOT / "assets/source/lightcycle_rider_check.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(out))
        print(f"saved {out}")
    sys.exit(0 if not fails else 1)


main()
