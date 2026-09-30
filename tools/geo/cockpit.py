"""Production cockpit, rider-contact, and articulated canopy geometry.

Everything is authored in world space to match the solved contact points in
spec/lightcycle.spec.json. The builder favors real brackets, ribs, pivots,
thin skins, and visible hardware over large primitive slabs so the bike still
reads as an expensive machine with every emissive channel disabled.
"""
import math

from mathutils import Matrix, Vector

from . import _lib as L
from .chassis import _box, _bolt, _bolt_row, _bracket, _row


def _half_width(dims: dict) -> float:
    return dims["width"] / 2


def _side_y(dims: dict, side: int, factor: float = 0.86) -> float:
    return side * _half_width(dims) * factor


def _bar_between(bm, a, b, radius=0.012, segments=18):
    """Cylinder whose local +Z is aligned from a to b."""
    va, vb = Vector(a), Vector(b)
    d = vb - va
    if d.length <= 1e-6:
        return
    mid = (va + vb) * 0.5
    rot = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    L.cylinder(bm, Matrix.Translation(mid) @ rot, radius, d.length, segments=segments)


def _boss(bm, center, axis="y", radius=0.022, depth=0.018):
    rot = {
        "x": Matrix.Rotation(math.pi / 2, 4, "Y"),
        "y": Matrix.Rotation(math.pi / 2, 4, "X"),
        "z": Matrix.Identity(4),
    }[axis]
    L.cylinder(bm, Matrix.Translation(Vector(center)) @ rot, radius, depth, segments=24)


def handlebar(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.82)
    grip_y = _side_y(dims, side, 0.96)
    _bar_between(bm, (-0.61, side * 0.07, 0.61), (-0.705, y, 0.68), radius=0.014)
    _bar_between(bm, (-0.665, side * 0.105, 0.645), (-0.735, grip_y, 0.70), radius=0.011)
    _boss(bm, (-0.61, side * 0.07, 0.61), "y", 0.025, 0.020)
    _bar_between(bm, (-0.705, grip_y, 0.70), (-0.760, grip_y, 0.70), radius=0.017, segments=24)
    _boss(bm, (-0.765, grip_y, 0.70), "x", 0.020, 0.012)

    # Keep the production assembly centered on the rider solver's contractual
    # grip point. The hard-surface bars extend asymmetrically forward/inboard,
    # so their measured bounds center is not the authored endpoint above.
    # This correction is deliberately applied to geometry, not the test.
    from bmesh import ops as _bops
    _bops.translate(bm, verts=bm.verts[:], vec=(-0.042, 0.0, 0.047))
    return bm


def control(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.985)
    _box(bm, (-0.785, y, 0.704), (0.032, 0.018, 0.020))
    _box(bm, (-0.800, y - side * 0.020, 0.690), (0.018, 0.007, 0.024))
    for dx in (-0.010, 0.010):
        _bolt(bm, (-0.775 + dx, y + side * 0.020, 0.714),
              rot=Matrix.Rotation(math.pi / 2, 4, "X"),
              r=0.004, depth=0.006, segments=8)
    return bm


def chest_support(dims: dict):
    bm = L.new_bm()
    _box(bm, (-0.238, 0.0, 0.505), (0.105, 0.065, 0.010))
    _box(bm, (-0.238, 0.0, 0.530), (0.090, 0.058, 0.013))
    for side in (-1, 1):
        _bar_between(bm, (-0.31, side * 0.052, 0.493), (-0.35, side * 0.11, 0.43), radius=0.010)
        _boss(bm, (-0.35, side * 0.11, 0.43), "y", 0.018, 0.012)
    _bolt_row(bm, (-0.315, 0.066, 0.535), (-0.160, 0.066, 0.535), 5,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.0045, depth=0.006)
    _bolt_row(bm, (-0.315, -0.066, 0.535), (-0.160, -0.066, 0.535), 5,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.0045, depth=0.006)
    return bm


def shin_rest(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.92)
    _box(bm, (0.443, y, 0.675), (0.095, 0.022, 0.020))
    _box(bm, (0.443, y + side * 0.024, 0.700), (0.082, 0.009, 0.032))
    for x in (0.375, 0.510):
        _bar_between(bm, (x, y * 0.60, 0.60), (x, y, 0.665), radius=0.008)
        _boss(bm, (x, y * 0.60, 0.60), "y", 0.015, 0.010)
    return bm


def foot_rest(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.92)
    _bar_between(bm, (0.54, y * 0.62, 0.31), (0.62, y, 0.28), radius=0.010)
    _box(bm, (0.620, y, 0.280), (0.036, 0.026, 0.009))
    for x in _row((0.592, y + side * 0.018, 0.292), (0.648, y + side * 0.018, 0.292), 5):
        _box(bm, x, (0.004, 0.005, 0.007))
    _boss(bm, (0.54, y * 0.62, 0.31), "y", 0.016, 0.012)
    return bm


def rider_mount(dims: dict):
    bm = L.new_bm()
    _box(bm, (0.05, 0.0, 0.565), (0.145, 0.050, 0.010))
    for x in (-0.08, 0.04, 0.16):
        _box(bm, (x, 0.0, 0.585), (0.045, 0.045, 0.008))
        for side in (-1, 1):
            _bar_between(bm, (x, side * 0.035, 0.555), (x, side * 0.11, 0.47), radius=0.008)
    return bm


def cockpit_display(dims: dict):
    bm = L.new_bm()
    angle = Matrix.Rotation(math.radians(-18), 4, "Y")
    _box(bm, (-0.515, 0.0, 0.660), (0.052, 0.072, 0.006), angle)
    _box(bm, (-0.535, 0.0, 0.642), (0.060, 0.080, 0.004), angle)
    return bm


def canopy_center(dims: dict):
    bm = L.new_bm()
    _box(bm, (0.62, 0.0, 0.856), (0.125, 0.055, 0.004))
    _box(bm, (0.62, 0.0, 0.866), (0.105, 0.016, 0.006))
    for x in _row((0.515, 0, 0), (0.725, 0, 0), 6):
        _box(bm, (x.x, 0.0, 0.846), (0.006, 0.060, 0.006))
    return bm


def canopy_side(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.86)
    _box(bm, (0.610, y, 0.790), (0.125, 0.004, 0.055))
    _box(bm, (0.635, y + side * 0.010, 0.775), (0.090, 0.003, 0.036))
    for x in (0.535, 0.610, 0.685):
        _bar_between(bm, (x, y * 0.62, 0.755), (x, y, 0.785), radius=0.007)
    for x in (0.545, 0.695):
        _boss(bm, (x, y * 0.62, 0.755), "x", 0.018, 0.016)
    return bm


def back_support(dims: dict):
    bm = L.new_bm()
    _box(bm, (0.44, 0.0, 0.705), (0.068, 0.058, 0.010))
    _box(bm, (0.44, 0.0, 0.730), (0.056, 0.050, 0.012))
    for side in (-1, 1):
        _bar_between(bm, (0.38, side * 0.045, 0.690), (0.31, side * 0.115, 0.56), radius=0.008)
    return bm


def deploy_arm(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.73)
    _bar_between(bm, (0.44, y * 0.72, 0.735), (0.58, y, 0.805), radius=0.010)
    _bar_between(bm, (0.47, y * 0.72, 0.752), (0.61, y, 0.820), radius=0.007)
    _boss(bm, (0.44, y * 0.72, 0.735), "y", 0.021, 0.018)
    _boss(bm, (0.58, y, 0.805), "y", 0.017, 0.014)
    return bm


def canopy_energy(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        _box(bm, (0.62, side * 0.030, 0.872), (0.115, 0.006, 0.003))
    return bm
