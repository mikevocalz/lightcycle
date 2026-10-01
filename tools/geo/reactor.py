"""Central reactor: the hero detail.

Authored in a REACTOR-LOCAL frame (origin at the core, main axis +Y) and placed
by the dispatcher. The main rings share the wheels' lateral axis so the mechanism
reads as a circular assembly from the side, which is where the concept boards put
it - an axis along the bike's length would show only edge-on rings.

The doc requires this to be interesting with emissions OFF, so the read comes
from nested precision rings, gimbal yokes, bearing lands, aperture blades and
cooling structure - not from the glow.
"""
import math

from mathutils import Matrix

from . import _lib as L

_Y = Matrix.Rotation(math.pi / 2, 4, "X")   # Z-axis primitive re-aimed along Y
_X = Matrix.Rotation(math.pi / 2, 4, "Y")


def _ring(z0, z1, hw):
    return [(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)]


def _ibeam(r_in, r_out, hw, web=0.35):
    """An I-section reads as a machined precision ring rather than a tube."""
    t = (r_out - r_in) * 0.28
    hwv = hw * web
    return [
        (-hw, r_in), (hw, r_in), (hw, r_in + t), (hwv, r_in + t),
        (hwv, r_out - t), (hw, r_out - t), (hw, r_out), (-hw, r_out),
        (-hw, r_out - t), (-hwv, r_out - t), (-hwv, r_in + t), (-hw, r_in + t),
    ]


def core():
    """Suspended core: faceted body with a machined equatorial band and the
    retaining claws that hold it in the field."""
    bm = L.new_bm()
    L.cylinder(bm, _Y, 0.052, 0.062, segments=16)            # faceted body
    L.revolve(bm, _ring(0.050, 0.058, 0.010), segments=32, axis="y")  # equator band
    L.radial(bm, lambda b, m: L.box(b, m, (0.016, 0.014, 0.020)), 8, 0.055, axis="y")
    return bm


def ring(index):
    """Three nested precision rings, each on its own bearing land."""
    r = (0.085, 0.107, 0.129)[index]
    bm = L.new_bm()
    L.revolve(bm, _ibeam(r - 0.011, r + 0.011, 0.016), segments=64, axis="y")
    # Radial slots cut the mass visually and read as balance/cooling features.
    n = (12, 16, 20)[index]
    L.radial(bm, lambda b, m: L.box(b, m, (0.013, 0.036, 0.007)), n, r, axis="y")
    # Bearing land: a raised rib the next ring rides on.
    L.revolve(bm, _ring(r + 0.011, r + 0.014, 0.006), segments=64, axis="y")
    return bm


def gyro(axis):
    """Three orthogonal gimbal rings with pivot bosses at their poles - the thing
    that makes the assembly read as a gyroscope and not three stacked discs."""
    bm = L.new_bm()
    r = 0.165
    L.revolve(bm, _ibeam(r - 0.008, r + 0.008, 0.011, web=0.30), segments=72, axis=axis)
    L.radial(bm, lambda b, m: L.box(b, m, (0.010, 0.026, 0.006)), 24, r, axis=axis)

    # Pivot bosses sit on the two axes perpendicular to this ring's own.
    perp = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}[axis]
    for p in perp[:1]:
        vec = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[p]
        for s in (1, -1):
            loc = tuple(c * r * s for c in vec)
            rot = {"x": _X, "y": _Y, "z": Matrix.Identity(4)}[p]
            L.cylinder(bm, Matrix.Translation(loc) @ rot, 0.016, 0.040, segments=14)
    return bm


def housing():
    """Open containment cheeks expose the nested rings through annular windows.

    Inner bearing lips connect to the outer shroud through six narrow webs.
    Cooling and parked aperture blades occupy the perimeter, leaving the moving
    precision rings visible from either side of the complete assembly.
    """
    bm = L.new_bm()
    L.revolve(bm, _ring(0.178, 0.200, 0.058), segments=72, axis="y")       # shroud
    for lat in (0.052, -0.052):
        for inner, outer in ((0.062, 0.073), (0.164, 0.182)):
            L.revolve(bm, [(lat - 0.006, inner), (lat + 0.006, inner),
                           (lat + 0.006, outer), (lat - 0.006, outer)],
                      segments=72, axis="y")
        # Actual open windows between structural webs, not dark painted slots.
        L.radial(bm, lambda b, m: L.box(b, m, (0.009, 0.012, 0.093)),
                 6, 0.1185, axis="y", along=lat, phase=math.pi / 6)
    # Compact cooling fins remain on the outer lips rather than covering rings.
    for lat in (0.070, -0.070):
        L.radial(bm, lambda b, m: L.box(b, m, (0.025, 0.008, 0.016)),
                 24, 0.175, axis="y", along=lat)
    # Radial struts tying shroud to plates.
    L.radial(bm, lambda b, m: L.box(b, m, (0.026, 0.104, 0.020)), 8, 0.190, axis="y")
    # Overlapping shield blades are parked outside the outer moving ring in
    # the authored rest pose, retaining their closing-mechanism construction.
    def blade(b, m):
        L.box(b, m @ Matrix.Rotation(math.radians(24), 4, "Y"), (0.050, 0.005, 0.026))

    L.radial(bm, blade, 14, 0.174, axis="y", along=0.040)
    # Fastener circle on the shroud.
    L.radial(bm, lambda b, m: L.cylinder(b, m @ _Y, 0.0075, 0.124, segments=10),
             16, 0.192, axis="y")
    return bm


def energy():
    """Conduits carrying energy out to the wheels and the trail emitter. Recessed
    channels, so with emission off they still read as plumbing."""
    bm = L.new_bm()
    for lat in (0.030, -0.030):
        L.revolve(bm, [(lat - 0.006, 0.146), (lat + 0.006, 0.146),
                       (lat + 0.006, 0.156), (lat - 0.006, 0.156)],
                  segments=72, axis="y")
    L.radial(bm, lambda b, m: L.box(b, m, (0.044, 0.010, 0.008)), 10, 0.170, axis="y")
    return bm
