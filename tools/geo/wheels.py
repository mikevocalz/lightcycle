"""Front and rear wheel assemblies: hubless perimeter design.

Authored in an AXLE-LOCAL frame: origin at the axle centre, axle along +Y
(the bike's lateral axis), radius measured in the XZ plane. The dispatcher
translates the finished shell onto the real axle. Spinning a wheel about X
instead mounts it sideways, which is the bug this frame exists to prevent.

The 1982 silhouette lives almost entirely in these two masses, so they carry the
most geometry. Hubless means the centre is genuinely open - the tyre rides a
perimeter stator on radial webs and roller bearings, with nothing in the middle.
"""
import math

import bmesh
from mathutils import Matrix

from . import _lib as L

_Y = Matrix.Rotation(math.pi / 2, 4, "X")  # a Z-axis primitive re-aimed along Y


def _mirror(half):
    """half runs crown -> bead on +lateral. Mirror back to close the loop."""
    return list(half) + [(-y, z) for y, z in reversed(half[1:-1])] + [(-half[-1][0], half[-1][1])]


def _tyre_profile(R, hw, bead_r):
    """Crowned contact patch, shoulder radius, sidewall taper, square bead - the
    shape a real high-performance carcass takes under load."""
    k = hw / 0.15
    half = [
        (0.000, R), (0.055 * k, R - 0.0004), (0.098 * k, R - 0.0018), (0.126 * k, R - 0.0072),
        (0.1424 * k, R - 0.0175), (0.1470 * k, R - 0.0310), (0.1485 * k, R - 0.0520),
        (0.1470 * k, R - 0.0730), (0.1390 * k, R - 0.0900),
        (0.1240 * k, bead_r + 0.004), (0.1050 * k, bead_r),
    ]
    return _mirror(half)


def _ring(z0, z1, hw):
    return [(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)]


def tyre(c):
    bm = L.new_bm()
    R = c["R"]
    L.revolve(bm, _tyre_profile(R, c["hw"], c["bead_r"]), segments=96, axis="y")
    # Circumferential tread ribs keep the contact surface off pure-smooth, so the
    # wheel never reads as a neon disc.
    rib_lat = c["hw"] * .35
    for lat in (-rib_lat, rib_lat):
        L.revolve(bm, [(lat - 0.009, R + 0.0008), (lat + 0.009, R + 0.0008),
                       (lat + 0.009, R + 0.0022), (lat - 0.009, R + 0.0022)],
                  segments=96, axis="y")
    return bm


def stator(c):
    """The perimeter rail the wheel runs on, plus its radial webs."""
    bm = L.new_bm()
    br, inner = c["bead_r"], c["hub_r"] + 0.022
    L.revolve(bm, _ring(br - 0.004, br, 0.100), segments=96, axis="y")
    L.revolve(bm, _ring(inner, inner + 0.016, 0.092), segments=96, axis="y")

    span = (br - 0.004) - (inner + 0.016)
    mid = (inner + 0.016) + span / 2
    L.radial(bm, lambda b, m: L.box(b, m, (span, 0.026, 0.070)), c["webs"], mid, axis="y")

    def boss(b, m):
        L.cylinder(b, m @ _Y, 0.0105, 0.030, segments=12)

    for lat in (0.101, -0.101):
        L.radial(bm, boss, c["webs"], br - 0.016, axis="y", along=lat)
    return bm


def bearing(c):
    """Two races with real rollers between them."""
    bm = L.new_bm()
    hr = c["hub_r"]
    L.revolve(bm, _ring(hr + 0.004, hr + 0.014, 0.072), segments=72, axis="y")
    L.revolve(bm, _ring(hr - 0.014, hr - 0.004, 0.072), segments=72, axis="y")
    L.radial(bm, lambda b, m: L.cylinder(b, m @ _Y, 0.0072, 0.104, segments=10),
             c["rollers"], hr, axis="y")
    return bm


def energy_ring(c):
    """A recessed channel, so the glow sits INSIDE machined geometry rather than
    floating on the surface - the difference between energy and a decal."""
    bm = L.new_bm()
    r = c["hub_r"] + 0.030
    energy_lat = max(.062, c["hw"] * .68)
    for lat in (-energy_lat, energy_lat):
        L.revolve(bm, [(lat - 0.008, r), (lat + 0.008, r),
                       (lat + 0.008, r + 0.014), (lat - 0.008, r + 0.014)],
                  segments=96, axis="y")
    return bm


def brake_disc(c):
    bm = L.new_bm()
    hr = c["hub_r"]
    L.revolve(bm, _ring(hr - 0.075, hr - 0.016, 0.0055), segments=72, axis="y")
    # Directional vanes read as a real ventilated disc at macro range.
    L.radial(bm, lambda b, m: L.box(b, m, (0.052, 0.0100, 0.011)),
             30, hr - 0.046, axis="y", along=0.0085)
    return bm


def caliper(c, side):
    """Straddles the disc at the top of the hub void."""
    bm = L.new_bm()
    r = c["hub_r"] - 0.046
    y = min(0.120, c["hw"] * .55) * side
    L.box(bm, Matrix.Translation((0, y, r)), (0.108, 0.044, 0.088))
    L.box(bm, Matrix.Translation((0, y, r + 0.058)), (0.030, 0.036, 0.060))
    for dx in (-0.030, 0.030):
        L.cylinder(bm, Matrix.Translation((dx, y + 0.019 * side, r)) @ _Y,
                   0.0155, 0.016, segments=14)
    for dx in (-0.044, 0.044):
        L.cylinder(bm, Matrix.Translation((dx, y, r + 0.030)), 0.0062, 0.050, segments=10)
    return bm


def suspension(c, toward):
    """A milled arm carrying the stator inboard, with lightening pockets."""
    bm = L.new_bm()
    r, length = c["hub_r"] + 0.030, 0.30
    cx = toward * (length / 2)
    L.box(bm, Matrix.Translation((cx, 0, r)), (length, 0.074, 0.062))
    L.box(bm, Matrix.Translation((cx, 0, r)), (length * 0.82, 0.098, 0.030))
    for i in (-1, 0, 1):
        L.cylinder(bm, Matrix.Translation((cx + i * 0.072, 0, r)) @ _Y,
                   0.0175, 0.090, segments=14)
    L.cylinder(bm, Matrix.Translation((0, 0, r)) @ _Y, 0.030, 0.108, segments=20)
    return bm


def rear_drive(c):
    """Heavier than the front by design - it drives the wheel and feeds the trail."""
    bm = L.new_bm()
    hr = c["hub_r"]
    L.cylinder(bm, Matrix.Translation((0, 0, hr - 0.010)) @ _Y, 0.086, 0.140, segments=32)
    L.cylinder(bm, Matrix.Translation((0, 0, hr - 0.010)) @ _Y, 0.098, 0.052, segments=32)
    L.radial(bm, lambda b, m: L.box(b, m, (0.030, 0.012, 0.130)), 18, hr + 0.020, axis="y")
    return bm


def steering_yoke(c):
    bm = L.new_bm()
    r = c["hub_r"] + 0.090
    L.box(bm, Matrix.Translation((0, 0, r)), (0.130, 0.190, 0.048))
    for s in (-1, 1):
        L.box(bm, Matrix.Translation((0, 0.082 * s, r - 0.044)), (0.090, 0.030, 0.076))
    L.cylinder(bm, Matrix.Translation((0, 0, r)) @ _Y, 0.026, 0.200, segments=18)
    return bm
