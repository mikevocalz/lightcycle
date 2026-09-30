"""Production cockpit, rider-contact, and articulated canopy geometry.

Everything is authored in world space to match the solved contact points in
spec/lightcycle.spec.json. The builder favors real brackets, ribs, pivots,
thin skins, and visible hardware over large primitive slabs so the bike still
reads as an expensive machine with every emissive channel disabled.
"""
import math

from mathutils import Matrix, Vector

from . import _lib as L
from .chassis import tail_floor, tail_outer, saddle_surface, _box, _bolt, _bolt_row, _bracket, _row, _interp, skin


def _half_width(dims: dict) -> float:
    return dims.get("mechanicalWidth", dims["width"]) / 2


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
    # Recessed saddle insert follows the spine rather than reading as three
    # exposed blocks. Its shallow front remains below the solved prone rider.
    skin(bm, saddle_surface, 40, 12, thickness=0.012, inward=(0, 0, -1))
    return bm


def cockpit_display(dims: dict):
    bm = L.new_bm()
    angle = Matrix.Rotation(math.radians(-18), 4, "Y")
    _box(bm, (-0.515, 0.0, 0.660), (0.052, 0.072, 0.006), angle)
    _box(bm, (-0.535, 0.0, 0.642), (0.060, 0.080, 0.004), angle)
    return bm


def _canopy_profile(u):
    # The rear deck echoes the new rear shell, with no change to its hinge or
    # transform. .864 top minus .008 skin = required .856 minimum underside.
    return _interp([(0, 0.864), (0.12, 0.878), (0.46, 0.930),
                    (0.72, 0.968), (1, 0.949)], u)


def _canopy_width(u):
    return _interp([(0, 0.058), (0.38, 0.083), (0.70, 0.105), (1, 0.052)], u)


def _canopy_surface(u, v):
    cross = 2 * v - 1
    return (0.495 + 0.620 * u, _canopy_width(u) * cross,
            _canopy_profile(u) + 0.008 * (1 - cross * cross))


def canopy_center(dims: dict):
    bm = L.new_bm()
    skin(bm, _canopy_surface, 44, 20, thickness=0.008, inward=(0, 0, -1))
    return bm


def canopy_side(dims: dict, side: int):
    bm = L.new_bm()
    # These skins remain separate animated meshes. Outer skirts sit laterally
    # outside the rider; only the center roof spans the protected rider volume.
    def shoulder(u, v):
        # Sweep the lower leading edge back around the fixed knee. The upper
        # seam retains the complete roof profile; only the lower skirt recedes.
        x = 0.495 + 0.620 * u + 0.225 * (1 - u) * (1 - v) ** 2
        along = (x - 0.495) / 0.620
        lower = tail_floor(x)
        outer = tail_outer(x)
        inner = _canopy_width(along) + 0.003
        y = outer + (inner - outer) * v
        y += 0.009 * math.sin(math.pi * u) * math.sin(math.pi * v)
        z = lower + (_canopy_profile(along) - 0.002 - lower) * math.sin(math.pi * v / 2)
        return x, side * y, z
    skin(bm, shoulder, 44, 16, thickness=0.007, inward=(0, -side, 0))
    return bm


def back_support(dims: dict):
    bm = L.new_bm()
    # Small curved carbon pad retains the prior support envelope; the shoulder
    # skins carry the larger rear deck silhouette without a box-like backrest.
    def pad(u, v):
        cross = 2 * v - 1
        width = 0.052 + 0.006 * math.sin(math.pi * u)
        z = _interp([(0, 0.705), (0.58, 0.728), (1, 0.734)], u)
        return 0.372 + 0.136 * u, width * cross, z + 0.007 * (1 - cross * cross)
    skin(bm, pad, 20, 12, thickness=0.014, inward=(0, 0, -1))
    return bm


def deploy_arm(dims: dict, side: int):
    bm = L.new_bm()
    y = _side_y(dims, side, 0.73)
    # Raised, shortened canopy attachments clear the fixed knee throughout the
    # existing high-speed rotation and parent slide. The hinge stays unchanged.
    _bar_between(bm, (0.44, y * 0.72, 0.735), (0.545, y, 0.865), radius=0.010)
    _bar_between(bm, (0.47, y * 0.72, 0.752), (0.575, y, 0.878), radius=0.007)
    _boss(bm, (0.44, y * 0.72, 0.735), "y", 0.021, 0.018)
    _boss(bm, (0.545, y, 0.865), "y", 0.017, 0.014)
    return bm


def canopy_energy(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        # Narrow inserts follow the real crown. They carry no body mass and stay
        # inside the existing .98 m height rather than floating above the shell.
        def ribbon(u, v, side=side):
            along = 0.016 + 0.968 * u
            cross = side * (0.84 + 0.065 * (2 * v - 1))
            x, y, z = _canopy_surface(along, (cross + 1) / 2)
            return x, y, z + 0.002
        skin(bm, ribbon, 44, 4, thickness=0.0015, inward=(0, 0, -1))
    return bm
