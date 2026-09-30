"""Production emissive inserts.

These meshes stay neutral in the authored GLB. Player hue is always applied at
runtime by the renderer adapters; geometry only defines where energy can appear.
"""
import math

from mathutils import Matrix

from . import _lib as L
from .chassis import _box


def _strip_pair(bm, x: float, z: float, hx: float, y: float, hz: float):
    for side in (-1, 1):
        _box(bm, (x, side * y, z), (hx, 0.003, hz))


def body_primary(dims: dict):
    bm = L.new_bm()
    y = (dims["width"] / 2) * 0.99
    for x, hx in ((-0.46, 0.18), (-0.02, 0.20), (0.42, 0.17)):
        _strip_pair(bm, x, 0.555, hx, y, 0.009)
    return bm


def body_secondary(dims: dict):
    bm = L.new_bm()
    y = (dims["width"] / 2) * 0.94
    for x, hx in ((-0.30, 0.14), (0.10, 0.18), (0.48, 0.10)):
        _strip_pair(bm, x, 0.395, hx, y, 0.004)
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
    y = (dims["width"] / 2) * 0.80
    for side in (-1, 1):
        for x in (0.235, 0.300, 0.365):
            _box(bm, (x, side * y, 0.40), (0.008, 0.003, 0.075))
    return bm


def cockpit(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        _box(bm, (-0.515, side * 0.038, 0.665), (0.038, 0.004, 0.003))
    return bm


def rear(dims: dict):
    bm = L.new_bm()
    for side in (-1, 1):
        _box(bm, (0.830, side * 0.072, 0.585), (0.018, 0.012, 0.024))
    return bm


def trail_port(dims: dict):
    bm = L.new_bm()
    _box(bm, (0.895, 0.0, 0.460), (0.008, 0.055, 0.034))
    for side in (-1, 1):
        _box(bm, (0.888, side * 0.060, 0.460), (0.016, 0.004, 0.040))
    return bm
