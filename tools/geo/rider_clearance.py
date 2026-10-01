"""Fixed-rider capsule constraints for shell authoring, in Blender coordinates.

All joints come from the existing rider solver. Queries intersect a line with
the exact rounded capsule (segment swept by a sphere), expanded by the modeling
margin. They constrain candidate points; they do not certify mesh interiors,
animation sweeps, ergonomics outside the fixed pose, or human fit variation.
"""
from functools import lru_cache
import math
from typing import NamedTuple

from rider_proxy import ANTHRO, ARM_Y, LEG_Y, SPEC, solve_rider

MODELING_MARGIN = 0.005


class RiderCapsule(NamedTuple):
    name: str
    a: tuple[float, float, float]
    b: tuple[float, float, float]
    radius: float


@lru_cache(maxsize=1)
def rider_capsules():
    """The authoritative solved pose, with the radii used by build_rider()."""
    contacts = SPEC["dimensions_m"]["riderEnvelope"]["contactPoints"]
    joints, arm, leg = solve_rider(
        (0.02, 0.62),
        {"grip": tuple(contacts["grip"]), "peg": tuple(contacts["footPeg"])},
    )
    if arm != "ok" or leg != "ok":
        raise ValueError(f"Fixed rider solve failed: {arm}, {leg}")
    result = []

    def add(name, first, second, radius, y=0):
        a, b = joints[first], joints[second]
        result.append(RiderCapsule(name, (a[0], y, a[1]), (b[0], y, b[1]), radius))

    add("torso", "hip", "shoulder", ANTHRO["chest_depth"] / 2)
    add("head", "shoulder", "head", 0.115)
    for side in (-1, 1):
        suffix = "L" if side > 0 else "R"
        add("upper_arm_" + suffix, "shoulder", "elbow", 0.052, side * ARM_Y)
        add("forearm_" + suffix, "elbow", "wrist", 0.045, side * ARM_Y)
        add("thigh_" + suffix, "hip", "knee", 0.075, side * LEG_Y)
        add("shin_" + suffix, "knee", "ankle", 0.055, side * LEG_Y)
        add("foot_" + suffix, "ankle", "ball", 0.045, side * LEG_Y)
    return tuple(result)


def point_capsule_margin(point, capsule):
    """Signed distance to the physical capsule surface; negative means inside."""
    d = tuple(b - a for a, b in zip(capsule.a, capsule.b))
    q = tuple(p - a for p, a in zip(point, capsule.a))
    length2 = sum(value * value for value in d)
    t = max(0.0, min(1.0, sum(x * y for x, y in zip(q, d)) / length2)) if length2 else 0.0
    return math.sqrt(sum((q[i] - t * d[i]) ** 2 for i in range(3))) - capsule.radius


def capsule_axis_interval(capsule, axis, fixed_point, margin=MODELING_MARGIN):
    """Closed capsule intersection interval along one coordinate axis, or None.

    fixed_point supplies the other two coordinates; its axis entry is ignored.
    The interval is the union of the finite cylinder and its two spherical caps.
    No rasterization or fitted joint constants are used.
    """
    if axis not in (0, 1, 2) or not math.isfinite(margin) or margin < 0:
        raise ValueError("axis must be 0/1/2 and margin finite/nonnegative")
    radius = capsule.radius + margin
    intervals = []
    for center in (capsule.a, capsule.b):
        remaining = radius * radius - sum((fixed_point[i] - center[i]) ** 2 for i in range(3) if i != axis)
        if remaining >= 0:
            delta = math.sqrt(remaining)
            intervals.append((center[axis] - delta, center[axis] + delta))

    d = tuple(b - a for a, b in zip(capsule.a, capsule.b))
    length2 = sum(value * value for value in d)
    if length2:
        base = tuple(0.0 if i == axis else fixed_point[i] for i in range(3))
        q = tuple(base[i] - capsule.a[i] for i in range(3))
        dot = sum(x * y for x, y in zip(q, d))
        aa = max(0.0, 1 - d[axis] * d[axis] / length2)
        bb = 2 * (q[axis] - dot * d[axis] / length2)
        cc = sum(value * value for value in q) - dot * dot / length2 - radius * radius
        cylinder = None
        if aa < 1e-12:
            if cc <= 0:
                cylinder = (-math.inf, math.inf)
        else:
            discriminant = bb * bb - 4 * aa * cc
            if discriminant >= 0:
                root = math.sqrt(discriminant)
                cylinder = ((-bb - root) / (2 * aa), (-bb + root) / (2 * aa))
        if cylinder:
            lo, hi = cylinder
            if abs(d[axis]) > 1e-12:
                ends = sorted((-dot / d[axis], (length2 - dot) / d[axis]))
                lo, hi = max(lo, ends[0]), min(hi, ends[1])
            elif not 0 <= dot / length2 <= 1:
                lo, hi = 1, 0
            if lo <= hi:
                intervals.append((lo, hi))
    if not intervals:
        return None
    return min(interval[0] for interval in intervals), max(interval[1] for interval in intervals)


def torso_underside_height_limit(x, y, margin=MODELING_MARGIN):
    """Maximum shell Z below the torso at (x,y), or None outside its projection."""
    torso = rider_capsules()[0]
    interval = capsule_axis_interval(torso, 2, (x, y, 0), margin)
    return interval[0] if interval else None


def torso_outside_lateral_min(x, z, margin=MODELING_MARGIN):
    """Minimum abs(Y) outside the torso at (x,z), or None when unconstrained."""
    torso = rider_capsules()[0]
    interval = capsule_axis_interval(torso, 1, (x, 0, z), margin)
    return max(abs(value) for value in interval) if interval else None


def limbs_inner_lateral_limit(x, z, margin=MODELING_MARGIN):
    """Maximum abs(Y) in the central corridor between mirrored arms and legs.

    This selects the inward side of the limbs. Outside/above/below solutions are
    also possible; use capsule_axis_interval for a different surfacing strategy.
    """
    limits = []
    for capsule in rider_capsules()[2:]:
        interval = capsule_axis_interval(capsule, 1, (x, 0, z), margin)
        if interval:
            lo, hi = interval
            limits.append(0.0 if lo <= 0 <= hi else min(abs(lo), abs(hi)))
    return min(limits) if limits else None
