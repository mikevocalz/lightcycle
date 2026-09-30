"""Front and rear wheel assemblies: hubless perimeter design.

The 1982 silhouette lives almost entirely in these two masses, so they get the
most geometry. Hubless means the centre is genuinely open - the tyre rides on a
perimeter stator carried by radial webs and roller bearings, with nothing in the
middle. A solid hub filled with a disc would kill the read instantly.

Sections are authored as (lateral, radius) profiles revolved about +X.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _lib as L


def _mirror_profile(half):
    """half runs crown -> bead on +y. Mirror it back along -y to close the loop."""
    return list(half) + [(-y, z) for y, z in reversed(half[1:-1])] + [(-half[-1][0], half[-1][1])]


# Tyre cross-section. Crowned contact patch, shoulder radius, sidewall taper,
# square bead - the shape a real high-performance carcass takes under load.
def _tyre_profile(R, hw, bead_r):
    half = [
        (0.000, R), (0.055, R - 0.0004), (0.098, R - 0.0018), (0.126, R - 0.0072),
        (0.1424 * (hw / 0.15), R - 0.0175), (0.1470 * (hw / 0.15), R - 0.0310),
        (0.1485 * (hw / 0.15), R - 0.0520), (0.1470 * (hw / 0.15), R - 0.0730),
        (0.1390 * (hw / 0.15), R - 0.0900), (0.1240 * (hw / 0.15), bead_r + 0.004),
        (0.1050 * (hw / 0.15), bead_r),
    ]
    return _mirror_profile(half)


def _ring_profile(z0, z1, hw):
    return [(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)]


def tyre(ctx, x):
    R, hw = ctx["R"], ctx["hw"]
    bm = L.new_bm()
    L.revolve(bm, _tyre_profile(R, hw, ctx["bead_r"]), segments=96, center=(x, 0, 0))
    # Circumferential tread grooves: shallow rings cut visually by raised ribs, so
    # the contact patch never reads as a smooth neon disc.
    for gy in (-0.052, 0.052):
        L.revolve(bm, _ring_profile(R + 0.0008, R + 0.0022, 0.009), segments=96,
                  center=(x + gy, 0, 0))
    return bm


def stator(ctx, x):
    """The perimeter rail the wheel actually runs on, plus its radial webs."""
    bm = L.new_bm()
    br = ctx["bead_r"]
    inner = ctx["hub_r"] + 0.022
    L.revolve(bm, _ring_profile(br - 0.004, br, 0.100), segments=96, center=(x, 0, 0))
    L.revolve(bm, _ring_profile(inner, inner + 0.016, 0.092), segments=96, center=(x, 0, 0))

    span = (br - 0.004) - (inner + 0.016)
    mid = (inner + 0.016) + span / 2

    def web(b, m):
        L.box(b, m, (0.070, 0.026, span))

    L.radial(bm, web, ctx["webs"], mid, axis="x", x=x)

    # Fastener bosses on the outer rail - service logic, visible at macro range.
    def boss(b, m):
        L.cylinder(b, m @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.0105, 0.030, segments=12)

    L.radial(bm, boss, ctx["webs"], br - 0.016, axis="x", x=x + 0.101)
    L.radial(bm, boss, ctx["webs"], br - 0.016, axis="x", x=x - 0.101)
    return bm


def bearing(ctx, x):
    """Two races with real rollers between them."""
    bm = L.new_bm()
    hr = ctx["hub_r"]
    L.revolve(bm, _ring_profile(hr + 0.004, hr + 0.014, 0.072), segments=72, center=(x, 0, 0))
    L.revolve(bm, _ring_profile(hr - 0.014, hr - 0.004, 0.072), segments=72, center=(x, 0, 0))

    def roller(b, m):
        L.cylinder(b, m @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.0072, 0.104, segments=10)

    L.radial(bm, roller, ctx["rollers"], hr, axis="x", x=x)
    return bm


def energy_ring(ctx, x):
    """A recessed channel, so the glow sits INSIDE machined geometry rather than
    floating on the surface. This is what keeps the energy reading as part of the
    machine instead of a decal."""
    bm = L.new_bm()
    r = ctx["hub_r"] + 0.030
    for gy in (-0.062, 0.062):
        L.revolve(bm, _ring_profile(r, r + 0.014, 0.008), segments=96, center=(x + gy, 0, 0))
    return bm


def brake_disc(ctx, x):
    bm = L.new_bm()
    hr = ctx["hub_r"]
    L.revolve(bm, _ring_profile(hr - 0.075, hr - 0.016, 0.0055), segments=72, center=(x, 0, 0))

    # Directional vanes on the inner face read as a real ventilated disc.
    def vane(b, m):
        L.box(b, m, (0.011, 0.0100, 0.052))

    L.radial(bm, vane, 30, hr - 0.046, axis="x", x=x + 0.0085)
    return bm


def _drill_cutter(ctx, x):
    """Cross-drilling for the disc. One boolean, not thirty."""
    bm = L.new_bm()

    def hole(b, m):
        L.cylinder(b, m @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.0052, 0.06, segments=8)

    for ring_r, n, ph in ((ctx["hub_r"] - 0.030, 20, 0.0), (ctx["hub_r"] - 0.058, 16, 0.18)):
        L.radial(bm, hole, n, ring_r, axis="x", x=x)
    return bm


def caliper(ctx, x, side):
    bm = L.new_bm()
    hr = ctx["hub_r"]
    y = 0.070 * side
    base = Matrix.Translation((x, y, hr - 0.046))
    L.box(bm, base, (0.088, 0.044, 0.108))
    L.box(bm, Matrix.Translation((x, y, hr + 0.012)), (0.060, 0.036, 0.030))
    for dz in (-0.030, 0.030):
        L.cylinder(bm, Matrix.Translation((x, y + 0.019 * side, hr - 0.046 + dz))
                   @ Matrix.Rotation(math.pi / 2, 4, "X"), 0.0155, 0.016, segments=14)
    for dz in (-0.044, 0.044):
        L.cylinder(bm, Matrix.Translation((x + 0.030, y, hr - 0.046 + dz))
                   @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.0062, 0.050, segments=10)
    return bm


def suspension(ctx, x, toward):
    """A milled arm carrying the stator into the chassis, with lightening pockets."""
    bm = L.new_bm()
    hr = ctx["hub_r"]
    length = 0.30
    cx = x + toward * (length / 2)
    L.box(bm, Matrix.Translation((cx, 0, hr + 0.030)), (length, 0.074, 0.062))
    L.box(bm, Matrix.Translation((cx, 0, hr + 0.030)), (length * 0.82, 0.098, 0.030))
    for i in (-1, 0, 1):
        L.cylinder(bm, Matrix.Translation((cx + i * 0.072, 0, hr + 0.030))
                   @ Matrix.Rotation(math.pi / 2, 4, "X"), 0.0175, 0.090, segments=14)
    L.cylinder(bm, Matrix.Translation((x, 0, hr + 0.030)) @ Matrix.Rotation(math.pi / 2, 4, "X"),
               0.030, 0.108, segments=20)
    return bm


def rear_drive(ctx, x):
    """The rear is deliberately heavier than the front - it drives the wheel and
    feeds the trail emitter."""
    bm = L.new_bm()
    hr = ctx["hub_r"]
    L.cylinder(bm, Matrix.Translation((x, 0, hr - 0.010))
               @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.086, 0.140, segments=32)
    L.cylinder(bm, Matrix.Translation((x, 0, hr - 0.010))
               @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.098, 0.052, segments=32)

    def fin(b, m):
        L.box(b, m, (0.130, 0.012, 0.030))

    L.radial(bm, fin, 18, hr + 0.020, axis="x", x=x)
    return bm


def steering_yoke(ctx, x):
    bm = L.new_bm()
    hr = ctx["hub_r"]
    L.box(bm, Matrix.Translation((x, 0, hr + 0.090)), (0.130, 0.190, 0.048))
    for s in (-1, 1):
        L.box(bm, Matrix.Translation((x, 0.082 * s, hr + 0.046)), (0.090, 0.030, 0.076))
    L.cylinder(bm, Matrix.Translation((x, 0, hr + 0.090))
               @ Matrix.Rotation(math.pi / 2, 4, "X"), 0.026, 0.200, segments=18)
    return bm
