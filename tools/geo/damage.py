"""Independent sacrificial skins following the shared compound body surfaces.

Node names and physical origins are assigned by the canonical builder. These
patches remain separate meshes; none bridges or covers the reactor opening.
"""
from . import _lib as L
from .chassis import mid_surface, nose_surface, rear_surface, skin


def _patch(dims, side, surface, u0, u1, v0, v1, nu=24, nv=20):
    bm = L.new_bm()

    def shape(u, v):
        x, y, z = surface(dims, side, u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)
        # A narrow, consistent panel reveal rather than a floating flat plate.
        return x, y + side * 0.0035, z

    skin(bm, shape, nu, nv, 0.0025, (0, -side, 0))
    return bm


def nose(dims: dict, side: int):
    # Broad access skin on the trailing wedge, clear of the front energy band.
    return _patch(dims, side, nose_surface, 0.64, 0.94, 0.10, 0.55, 24, 24)


def mid(dims: dict, side: int, which: int):
    # The shared surface's circular boundary defines the aperture; preserving
    # its parameterization prevents a damage skin from sealing the opening.
    u0, u1 = (0.06, 0.43) if which == 1 else (0.48, 0.92)
    return _patch(dims, side, mid_surface, u0, u1, 0.09, 0.90, 16, 28)


def rear(dims: dict, side: int):
    return _patch(dims, side, rear_surface, 0.08, 0.86, 0.10, 0.62, 28, 14)


def reactor_cover(dims: dict):
    """Detachable peripheral housing bezel with a completely open center.

    Keep the existing positive-Y cover ownership and pivot. The inner radius
    clears the 0.20 m housing; the outer radius remains inside the 0.238 m body
    aperture. The core and all concentric machinery stay visible through it.
    """
    bm = L.new_bm()
    L.revolve(bm, [(0.184, 0.216), (0.191, 0.216),
                   (0.191, 0.232), (0.184, 0.232)],
              segments=96, axis="y", center=(0.30, 0.0, 0.40))
    return bm
