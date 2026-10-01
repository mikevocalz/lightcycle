"""Production emissive inserts.

These meshes stay neutral in the authored GLB. Player hue is always applied at
runtime by the renderer adapters; geometry only defines where energy can appear.
"""
import math

from mathutils import Matrix

from . import _lib as L
from .chassis import _box, _interp, _tail_end, nose_surface, rear_surface, sill_surface, coaming_surface, skin


def _nose_energy_u(dims, v):
    """Two long angular strokes; the shell supplies compound depth, not a wavy path."""
    z=.125+.815*v
    if z <= .709:
        x=-.678+(.260)*((z-.125)/(.709-.125))
    else:
        x=-.418-.417*((z-.709)/(.941-.709))
    front=nose_surface(dims,1,0,v)[0]
    back=nose_surface(dims,1,1,v)[0]
    return max(.11,min(.88,(x-front)/max(.001,back-front)))


def body_primary(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        def shape(s, across, side=side):
            v = 0.025 + 0.91 * s
            center_u = _nose_energy_u(dims, v)
            front = nose_surface(dims, side, 0.0, v)
            back = nose_surface(dims, side, 1.0, v)
            span = back[0] - front[0]
            # Preserve the band's perceived width through the sharp shoulder
            # diagonal; a constant U width becomes a tiny LED at the crown.
            v0, v1 = max(0.025, v - 0.002), min(0.935, v + 0.002)
            p0 = nose_surface(dims, side, _nose_energy_u(dims, v0), v0)
            p1 = nose_surface(dims, side, _nose_energy_u(dims, v1), v1)
            slope = (p1[0] - p0[0]) / max(0.0001, p1[2] - p0[2])
            width = _interp([(0.025, 0.042), (0.55, 0.056),
                             (0.78, 0.060), (0.935, 0.035)], v)
            half_u = width * 0.5 * math.hypot(1, slope) / max(span, 0.001)
            half_u = min(half_u, center_u - 0.02, 0.98 - center_u)
            u = center_u + (2 * across - 1) * half_u
            x, y, z = nose_surface(dims, side, u, v)
            return x, y + side * 0.0045, z
        skin(bm, shape, 64, 4, 0.003, (0, -side, 0))
    # Twin front-facing energy rails are a dominant feature of the exact front view.
    cx = -dims["wheelbase"] / 2
    for side in (-1, 1):
        def front_bar(u, v, side=side):
            z=.755+.190*u
            offset=_interp([(0,.390),(.55,.292),(1,.145)],u)
            x=cx+offset-.004
            y=side*(.137+.024*(2*v-1))
            return x,y,z
        skin(bm, front_bar, 30, 4, .0025, (1,0,0))
    return bm


def body_secondary(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        def sill(u, v, side=side):
            # Follow the carbon sill, below the complete reactor aperture.
            shell_u = 0.08 + 0.83 * u
            shell_v = 0.40 + 0.16 * v
            x, y, z = sill_surface(dims, side, shell_u, shell_v)
            return x, y + side * 0.004, z
        skin(bm, sill, 48, 2, 0.002, (0, -side, 0))
    return bm


def wheel_marker(dims: dict, front: bool):
    bm = L.new_bm()
    x = (-1 if front else 1) * dims["wheelbase"] / 2
    z = dims["wheelOuterDiameter"] / 2
    r = dims["hubVoidDiameter"] / 2 + 0.115
    for i in range(9):
        a = math.radians(-48 + i * 12)
        px = x + math.sin(a) * r
        pz = z + math.cos(a) * r
        rot = Matrix.Rotation(-a, 4, "Y")
        _box(bm, (px, 0.0, pz), (0.010, 0.004, 0.030), rot)
    return bm


def reactor(dims: dict):
    bm = L.new_bm()
    # Perimeter energy rings emphasize the housing; no strip crosses the core.
    rx, rz = dims.get("reactorCenterX", .30), dims.get("reactorCenterZ", .40)
    for side in (-1, 1):
        y = side * 0.184
        L.revolve(bm, [(y - 0.002, 0.205), (y + 0.002, 0.205),
                       (y + 0.002, 0.213), (y - 0.002, 0.213)],
                  segments=96, axis="y", center=(rx, 0.0, rz))
    return bm


def cockpit(dims: dict):
    bm = L.new_bm()
    for side in (-1,1):
        def insert(u,v,side=side):
            x,y,z=coaming_surface(dims,side,.018+.96*u,.52+.14*v)
            return x,y,z+.003
        skin(bm,insert,48,4,.002,(0,0,-1))
    return bm


def rear(dims: dict):
    bm = L.new_bm()
    # Central vertical rear blade from the exact tail/rear view.
    _box(bm, (_tail_end(dims)+.004, 0.0, .842), (.0035, .027, .090))
    for side in (-1, 1):
        def shape(u, v, side=side):
            x, y, z = rear_surface(dims, side, 0.40 + 0.55 * u, 0.72 + 0.10 * v)
            return x, y + side * 0.004, z
        skin(bm, shape, 30, 2, 0.0025, (0, -side, 0))
    return bm


def trail_port(dims: dict):
    bm = L.new_bm()
    x = _tail_end(dims) - .045
    _box(bm, (x, 0.0, 0.460), (0.008, 0.055, 0.034))
    for side in (-1, 1):
        _box(bm, (x-.007, side * 0.060, 0.460), (0.016, 0.004, 0.040))
    return bm
