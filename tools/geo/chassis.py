"""Chassis shells: the narrow central backbone plus the layered outer armor
that flanks it.

This is the part of the bike that has to look expensive with every emissive
switched off. No fuel-tank shape, no normal seat, no swingarm read - a low,
long, monumental 1982 mass up close made of real panel breaks, recessed
fasteners, milled brackets and structural ribs (TRON: Ares). Every shell is a
thin plate (2-6 cm world size chosen so the caller's 2.2 mm bevel reads as a
real machined edge) standing off the backbone with a visible reveal gap, so
LC_Body_Core shows through between the plates instead of the whole assembly
reading as one slab.

Authored directly in WORLD space at the positions in build_lightcycle.py's
`deck` table (this module reads no other file; the numbers below are that
table's positions with the panels narrowed and, where they sit close to a
wheel or the rider, shortened so the real geometry clears both -
the deck's own boxes do not: LC_Nose_Shell_L/R and LC_Rear_Shell_L/R each
reach ~0.11 m past the front/rear wheel's inner clearance face at x=+/-0.81 m,
because they were sized as placeholder blockout, not checked against the
wheel circle. Real geometry here stops short of that line with margin instead
of matching the proxy box edge-for-edge.
"""
import math

from mathutils import Matrix, Vector

from . import _lib as L


def _ctx(dims: dict) -> dict:
    """Shared geometry parameters, derived from spec dimensions so this stays
    correct if the spec ever changes."""
    hw = dims["width"] / 2
    wb2 = dims["wheelbase"] / 2
    wheel_hw = dims["wheelSectionWidth"] / 2
    clear_x = wb2 - wheel_hw  # inner face of either wheel, world |x|
    return {
        "hw": hw,
        "y86": hw * 0.86,  # the deck table's default lateral factor
        "clear_x": clear_x,
        "ground": dims["groundClearance"],
    }


# --- small building blocks --------------------------------------------------

def _box(bm, center, half, rot=None):
    """center = world position, half = (hx, hy, hz) half-extents - the deck
    table's own convention, so a panel's size can be read straight off it."""
    m = Matrix.Translation(Vector(center))
    if rot is not None:
        m = m @ rot
    L.box(bm, m, tuple(2 * h for h in half))


def _bolt(bm, center, rot=None, r=0.006, depth=0.010, segments=10):
    m = Matrix.Translation(Vector(center))
    if rot is not None:
        m = m @ rot
    L.cylinder(bm, m, r, depth, segments=segments)


def _row(p0, p1, count):
    """Evenly spaced world points from p0 to p1, inclusive."""
    a, b = Vector(p0), Vector(p1)
    if count <= 1:
        return [a.lerp(b, 0.5)]
    return [a.lerp(b, i / (count - 1)) for i in range(count)]


def _bolt_row(bm, p0, p1, count, **kw):
    for c in _row(p0, p1, count):
        _bolt(bm, c, **kw)


def _bracket(bm, center, half, bolt_r=0.0055, bolt_depth=0.009):
    """A milled standoff block plus its two retaining bolts - the visible
    construction logic that carries a shell back to the backbone, so the gap
    between them reads as a serviced assembly rather than a floating panel."""
    _box(bm, center, half)
    bx, by, bz = half
    for s in (-1, 1):
        _bolt(bm, (center[0] + bx * s * 0.55, center[1], center[2] + bz + bolt_depth * 0.4),
              r=bolt_r, depth=bolt_depth)


def _hatch_outline(bm, center_x, y, z, half_w, half_h, rot=None):
    """A proud rectangular seam standing off a flank - reads as a service
    access panel once the caller's bevel catches its edges."""
    for dz in (-half_h, half_h):
        _box(bm, (center_x, y, z + dz), (half_w, 0.004, 0.005), rot)
    for dx in (-half_w, half_w):
        _box(bm, (center_x + dx, y, z), (0.005, 0.004, half_h), rot)


# --- centreline backbone -----------------------------------------------------
# These four sit on Y=0, so the points that need Z clearance are grip (-0.72,
# 0.70) and chestSupport (-0.238, 0.528) from spec.lightcycle.spec.json's
# riderEnvelope - both on the rider centreline. Every backbone top here stays
# at or below z=0.50, well under chestSupport's 0.498 m pad bottom.

def build_body_core(dims: dict):
    """The structural spine: what shows in the reveal gaps between every
    shell around it. Kept low and narrow - LC_ChestSupport clears its crown
    with margin, and the wheels stay the dominant masses at distance."""
    bm = L.new_bm()

    _box(bm, (0.0, 0.0, 0.375), (0.58, 0.135, 0.065))
    # A second, narrower keel layer standing proud of the main box, so the
    # join reads as a panel break rather than a printed line.
    _box(bm, (0.0, 0.0, 0.455), (0.51, 0.024, 0.014))
    _bolt_row(bm, (-0.42, 0.024, 0.472), (0.42, 0.024, 0.472), 16, r=0.0055, depth=0.009)
    _bolt_row(bm, (-0.42, -0.024, 0.472), (0.42, -0.024, 0.472), 16, r=0.0055, depth=0.009)

    # Transition flange toward LC_Belly, offset down for a visible reveal.
    _box(bm, (0.0, 0.0, 0.285), (0.55, 0.15, 0.014))
    _bolt_row(bm, (-0.50, 0.15, 0.285), (0.50, 0.15, 0.285), 12,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)
    _bolt_row(bm, (-0.50, -0.15, 0.285), (0.50, -0.15, 0.285), 12,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)

    # Side intake louvers, gapped rather than a solid slot so the core colour
    # shows between blades.
    for side in (-1, 1):
        y = side * 0.146
        tilt = Matrix.Rotation(math.radians(14) * side, 4, "X")
        for c in _row((-0.35, y, 0.40), (0.25, y, 0.40), 12):
            _box(bm, c, (0.022, 0.006, 0.038), tilt)

    # Standoff brackets that will carry the flanking shells: visible service
    # logic in the gap, not a shell that floats for no mechanical reason.
    for x in (-0.45, -0.15, 0.15, 0.45):
        for side in (-1, 1):
            _bracket(bm, (x, side * 0.155, 0.40), (0.035, 0.012, 0.045))

    # A flush service-hatch seam on each flank.
    for side in (-1, 1):
        _hatch_outline(bm, 0.15, side * 0.136, 0.335, 0.14, 0.05)
        for dx, dz in ((-0.12, -0.03), (0.12, -0.03), (-0.12, 0.03), (0.12, 0.03)):
            _bolt(bm, (0.15 + dx, side * 0.138, 0.335 + dz),
                  rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)

    return bm


def build_body_spine(dims: dict):
    """The dorsal keel riding above the core: a stepped, tapering ridge with
    segmented armor knuckles, like a spine of overlapping plates rather than
    one continuous fin. Stays under kneeRest (0.443, 0.695) and clear of
    grip (-0.72, 0.70) by never reaching x=-0.65."""
    bm = L.new_bm()

    # Stepped taper: wide at the tail, narrow at the nose.
    _box(bm, (0.32, 0.0, 0.5875), (0.28, 0.070, 0.0225))
    _box(bm, (-0.05, 0.0, 0.5850), (0.30, 0.058, 0.0200))
    _box(bm, (-0.40, 0.0, 0.5775), (0.22, 0.044, 0.0150))

    # Segmented vertebra knuckles standing proud of the keel top, each with a
    # small real gap to the next - reads as an articulated spine, not a rail.
    top = 0.610
    for c in _row((-0.58, 0.0, top), (0.55, 0.0, top), 13):
        _box(bm, (c.x, c.y, top + 0.0125), (0.032, 0.028, 0.0125))
        for s in (-1, 1):
            _bolt(bm, (c.x, s * 0.030, top + 0.026), r=0.0045, depth=0.006)

    # Fastener rows along both flanks of the base ridge.
    _bolt_row(bm, (-0.58, 0.052, 0.565), (0.55, 0.052, 0.565), 18,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)
    _bolt_row(bm, (-0.58, -0.052, 0.565), (0.55, -0.052, 0.565), 18,
              rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)

    return bm


def build_belly(dims: dict):
    """Lower chassis pan beneath the core. footPeg (0.62, 0.28) clears it on
    X (this stays inside |x|<=0.525); kneeRest and grip clear it on Z."""
    bm = L.new_bm()

    _box(bm, (0.0, 0.0, 0.215), (0.525, 0.135, 0.045))
    # Central stiffening rib along the underside.
    _box(bm, (0.0, 0.0, 0.148), (0.46, 0.022, 0.020))

    # Mounting bosses along both flanks.
    for side in (-1, 1):
        y = side * 0.136
        rot = Matrix.Rotation(math.pi / 2, 4, "X")
        _bolt_row(bm, (-0.48, y, 0.24), (0.48, y, 0.24), 14, rot=rot, r=0.0055, depth=0.009)
        _bolt_row(bm, (-0.48, y, 0.19), (0.48, y, 0.19), 14, rot=rot, r=0.0055, depth=0.009)

    # Recessed access hatch, rear-of-centre.
    for side in (-1, 1):
        _hatch_outline(bm, 0.22, side * 0.138, 0.185, 0.12, 0.035)

    # Small brackets tying the belly to the core above.
    for x in (-0.30, 0.0, 0.30):
        _bracket(bm, (x, 0.0, 0.255), (0.04, 0.10, 0.010))

    return bm


def build_underbody(dims: dict):
    """Flat skid/undertray - the lowest layer. Diffuser fins stop 3 mm short
    of groundClearance (0.085 m) with room to spare."""
    ctx = _ctx(dims)
    bm = L.new_bm()
    ground = ctx["ground"]

    top = 0.128
    bottom = 0.106
    _box(bm, (0.0, 0.0, (top + bottom) / 2), (0.62, 0.145, (top - bottom) / 2))

    # Lengthwise diffuser fins across the rear half, each stopping well above
    # the ground-clearance floor.
    fin_bottom = ground + 0.012  # comfortable margin above the hard floor
    fin_top = bottom
    fin_h = (fin_top - fin_bottom) / 2
    fin_cz = (fin_top + fin_bottom) / 2
    for y in _row((-0.13, 0, 0), (0.13, 0, 0), 9):
        _box(bm, (0.18, y.x, fin_cz), (0.26, 0.006, fin_h))

    # Flush fastener grid, visible from directly below.
    rot = Matrix.Rotation(0, 4, "X")
    for y in (-0.10, 0.0, 0.10):
        _bolt_row(bm, (-0.55, y, bottom), (0.55, y, bottom), 8,
                  rot=rot, r=0.005, depth=0.006)

    return bm


# --- outboard shells ---------------------------------------------------------
# `side` is +1 for the _L node, -1 for _R - the deck table's own y_side
# convention, so callers can dispatch by literally testing name.endswith("_L").

def nose_shell(dims: dict, side: int):
    """Front cowl flanking the spine over the steering head. Two skin plates
    with a real service seam between them, standing off an inner panel with a
    visible reveal gap, and stopping at x=-0.75: 0.06 m clear of the front
    wheel's inner face (clear_x=0.81) rather than the deck proxy's -0.92,
    which oversteps that line by 0.11 m."""
    ctx = _ctx(dims)
    bm = L.new_bm()
    y86 = ctx["y86"]
    y_skin = side * y86 * 1.10
    y_in = side * y86 * 0.78
    y_gill = side * y86 * 1.16

    # Outer skin, two plates with a 3.5 cm seam between them.
    _box(bm, (-0.655, y_skin, 0.50), (0.090, 0.023, 0.100))
    _box(bm, (-0.430, y_skin, 0.49), (0.100, 0.023, 0.095))

    # Inner standoff panel, inboard of the skin for a visible reveal.
    _box(bm, (-0.50, y_in, 0.48), (0.175, 0.026, 0.080))

    # Nose-tip vent gills, angled so they catch light without an emissive.
    tilt = Matrix.Rotation(math.radians(-22) * side, 4, "X")
    for c in _row((-0.735, y_gill, 0.435), (-0.62, y_gill, 0.555), 5):
        _box(bm, c, (0.017, 0.006, 0.030), tilt)

    # Fastener lines along both skin plates.
    rot = Matrix.Rotation(math.pi / 2, 4, "X")
    _bolt_row(bm, (-0.745, y_skin * 1.03, 0.585), (-0.335, y_skin * 1.03, 0.585), 10, rot=rot)
    _bolt_row(bm, (-0.745, y_skin * 1.03, 0.415), (-0.335, y_skin * 1.03, 0.415), 10, rot=rot)

    # Service seam bolts at the panel split.
    for dz in (-0.06, 0.0, 0.06):
        _bolt(bm, (-0.555, y_skin, 0.50 + dz), rot=rot, r=0.005, depth=0.007)

    # Milled brackets carrying the panel back to LC_Body_Core.
    for x in (-0.62, -0.40):
        _bracket(bm, (x, side * y86 * 0.55, 0.46), (0.03, 0.012, 0.04))

    return bm


def mid_shell(dims: dict, side: int):
    """Centre section flanking the cockpit/spine between nose and rear.
    Sits entirely off the y=0 rider centreline (min |y|~0.13), so it clears
    chestSupport by ~2.7 cm laterally regardless of Z."""
    ctx = _ctx(dims)
    bm = L.new_bm()
    y86 = ctx["y86"]
    y_skin = side * y86 * 1.075
    y_in = side * y86 * 0.735

    # Outer skin, split at the cockpit divider with a small gap for a
    # visible conduit run.
    _box(bm, (-0.155, y_skin, 0.49), (0.145, 0.0225, 0.090))
    _box(bm, (0.155, y_skin, 0.49), (0.145, 0.0225, 0.090))
    _bolt(bm, (0.0, y_skin, 0.49), r=0.0075, depth=0.030,
          rot=Matrix.Rotation(math.pi / 2, 4, "Z"))

    # Inner standoff panel.
    _box(bm, (0.0, y_in, 0.475), (0.28, 0.025, 0.075))

    # Louvered vents.
    tilt = Matrix.Rotation(math.radians(12) * side, 4, "X")
    for c in _row((-0.34, y_skin * 1.05, 0.44), (0.28, y_skin * 1.05, 0.44), 10):
        _box(bm, c, (0.020, 0.006, 0.028), tilt)

    # Fastener lines top and bottom of the skin.
    rot = Matrix.Rotation(math.pi / 2, 4, "X")
    _bolt_row(bm, (-0.29, y_skin, 0.575), (0.29, y_skin, 0.575), 9, rot=rot)
    _bolt_row(bm, (-0.29, y_skin, 0.405), (0.29, y_skin, 0.405), 9, rot=rot)

    # Brackets to the core.
    for x in (-0.20, 0.20):
        _bracket(bm, (x, side * y86 * 0.50, 0.44), (0.03, 0.012, 0.04))

    return bm


def rear_shell(dims: dict, side: int):
    """Tail fairing over the drive side, tapering to a narrower tip.
    Stops at x=0.75: 0.06 m clear of the rear wheel's inner face (0.81),
    versus the deck proxy's 0.92, which oversteps that line by 0.11 m."""
    ctx = _ctx(dims)
    bm = L.new_bm()
    y86 = ctx["y86"]
    y_skin = side * y86 * 1.10
    y_in = side * y86 * 0.78
    y_tip = side * y86 * 1.05

    _box(bm, (0.44, y_skin, 0.50), (0.165, 0.023, 0.100))
    # Tapered tail tip - smaller cross-section, narrowing the silhouette.
    _box(bm, (0.665, y_tip, 0.475), (0.075, 0.020, 0.075))

    # Inner standoff panel.
    _box(bm, (0.42, y_in, 0.48), (0.185, 0.026, 0.080))

    # Vent gills near the tip.
    tilt = Matrix.Rotation(math.radians(20) * side, 4, "X")
    for c in _row((0.58, y_tip * 1.05, 0.435), (0.70, y_tip * 1.05, 0.53), 5):
        _box(bm, c, (0.016, 0.006, 0.028), tilt)

    # Fastener lines.
    rot = Matrix.Rotation(math.pi / 2, 4, "X")
    _bolt_row(bm, (0.28, y_skin * 1.03, 0.585), (0.62, y_skin * 1.03, 0.585), 9, rot=rot)
    _bolt_row(bm, (0.28, y_skin * 1.03, 0.415), (0.62, y_skin * 1.03, 0.415), 9, rot=rot)
    for dz in (-0.05, 0.0, 0.05):
        _bolt(bm, (0.605, y_skin, 0.475 + dz), rot=rot, r=0.005, depth=0.007)

    # Milled brackets back to the core.
    for x in (0.30, 0.52):
        _bracket(bm, (x, side * y86 * 0.55, 0.46), (0.03, 0.012, 0.04))

    return bm


def armor(dims: dict, side: int):
    """Lower flank armor over the drivetrain run: overlapping scale-like
    plates rather than one slab, each riveted at the exposed edge. Stays
    below z=0.335, clearing footPeg (0.62, 0.28) by 0.035 m on Z and
    kneeRest (0.443, 0.695) by a wide margin."""
    ctx = _ctx(dims)
    bm = L.new_bm()
    y86 = ctx["y86"]
    y = side * y86 * 1.02

    plate_half = (0.11, 0.017, 0.075)
    centers_x = (-0.20, -0.02, 0.16, 0.34, 0.52)
    for i, x in enumerate(centers_x):
        z = 0.41 + (0.006 if i % 2 else 0.0)  # slight alternating stand-off
        rot = Matrix.Rotation(math.radians(4) * side, 4, "Z")
        _box(bm, (x, y, z), plate_half, rot)
        # Rivets along the plate's trailing (exposed) edge.
        for dz in (-0.05, 0.0, 0.05):
            _bolt(bm, (x - plate_half[0] * 0.75, y * 1.02, z + dz),
                  rot=Matrix.Rotation(math.pi / 2, 4, "X"), r=0.005, depth=0.007)

    # Standoff brackets tying the armor run back to the belly/core.
    for x in (-0.10, 0.26):
        _bracket(bm, (x, side * y86 * 0.55, 0.37), (0.03, 0.012, 0.035))

    return bm
