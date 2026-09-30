"""Detachable production damage-panel geometry.

The base vehicle remains intact; these nodes are thin sacrificial outer skins
with their own pivots so LC_Damage and LC_Derez can move them independently.
"""
import math

from mathutils import Matrix

from . import _lib as L
from .chassis import _box, _bolt, _bolt_row


def _y(dims: dict, side: int, factor: float = 1.10) -> float:
    return side * (dims["width"] / 2) * 0.86 * factor


def _panel(dims: dict, x: float, side: int, z: float, hx: float, hz: float,
           seam: bool = True):
    bm = L.new_bm()
    y = _y(dims, side)
    _box(bm, (x, y, z), (hx, 0.002, hz))
    if seam:
        rot = Matrix.Rotation(math.pi / 2, 4, "X")
        count = max(3, int(hx / 0.035))
        _bolt_row(bm, (x - hx * 0.80, y + side * 0.004, z + hz * 0.78),
                  (x + hx * 0.80, y + side * 0.004, z + hz * 0.78),
                  count, rot=rot, r=0.004, depth=0.005, segments=8)
        _bolt_row(bm, (x - hx * 0.80, y + side * 0.004, z - hz * 0.78),
                  (x + hx * 0.80, y + side * 0.004, z - hz * 0.78),
                  count, rot=rot, r=0.004, depth=0.005, segments=8)
    return bm


def nose(dims: dict, side: int):
    return _panel(dims, -0.655, side, 0.50, 0.078, 0.082)


def mid(dims: dict, side: int, which: int):
    x = -0.155 if which == 1 else 0.155
    return _panel(dims, x, side, 0.49, 0.120, 0.074)


def rear(dims: dict, side: int):
    return _panel(dims, 0.610, side, 0.49, 0.090, 0.075)


def reactor_cover(dims: dict):
    bm = L.new_bm()
    y = (dims["width"] / 2) * 0.82
    for z in (0.30, 0.50):
        _box(bm, (0.30, y, z), (0.125, 0.003, 0.010))
    for x in (0.20, 0.40):
        _box(bm, (x, y, 0.40), (0.010, 0.003, 0.090))
    for dx in (-0.075, 0.075):
        for dz in (-0.060, 0.060):
            _bolt(bm, (0.30 + dx, y + 0.004, 0.40 + dz),
                  rot=Matrix.Rotation(math.pi / 2, 4, "X"),
                  r=0.005, depth=0.006, segments=8)
    return bm
