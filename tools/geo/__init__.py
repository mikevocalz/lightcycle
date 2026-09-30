"""Real hard-surface geometry, dispatched per node name.

Nodes with a builder here get production geometry; nodes without one keep their
blockout proxy. That lets the model be finished assembly by assembly while the
node contract, the validator, the manifest and both runtime adapters keep
working the whole way through - which is the point of the modular hierarchy.
"""
import bmesh

from . import _lib as L
from . import reactor
from . import wheels

__all__ = ["build_node", "handled", "L"]


def _ctx(dims, side):
    """Geometry parameters for one wheel end. The rear carries more structure -
    it drives the wheel and feeds the trail emitter."""
    return {
        "R": dims["wheelOuterDiameter"] / 2,
        "hw": dims["wheelSectionWidth"] / 2,
        "hub_r": dims["hubVoidDiameter"] / 2,
        "bead_r": dims["hubVoidDiameter"] / 2 + 0.085,
        "webs": 20 if side == "Front" else 24,
        "rollers": 44 if side == "Front" else 52,
    }


def _side_of(name):
    return "Front" if "Front" in name else "Rear"


_WHEEL = {
    "_OuterRing": wheels.tyre,
    "_InnerRing": wheels.stator,
    "_Bearing": wheels.bearing,
    "_EnergyRing": wheels.energy_ring,
    "_BrakeDisc": wheels.brake_disc,
}


def handled(name: str) -> bool:
    return build_node.__wrapped_names__(name)


# World position of the reactor centre; must match EMPTY_AT in build_lightcycle.
REACTOR_AT = (0.30, 0.0, 0.40)


def _lift(bm, x, dz):
    """Move an axle-local shell onto its real axle."""
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(x, 0.0, dz))
    return bm


def build_node(name: str, dims: dict, x_of):
    """Return a bmesh for `name`, or None to fall back to the blockout proxy.

    Wheel builders work in an axle-local frame (origin at the axle, axle along
    +Y); this places the finished shell on the real axle.
    """
    axle_z = dims["wheelOuterDiameter"] / 2

    def place(bm, name_for_x):
        return _lift(bm, x_of(name_for_x), axle_z)

    for suffix, fn in _WHEEL.items():
        if name.endswith(suffix) and "_Wheel_" in name:
            return place(fn(_ctx(dims, _side_of(name))), name)

    if "_Caliper_" in name:
        return place(wheels.caliper(_ctx(dims, _side_of(name)), 1 if name.endswith("_L") else -1), name)

    if name.endswith("_Suspension"):
        s = _side_of(name)
        # The arm reaches inboard toward the chassis, so it points the other way
        # at each end.
        return place(wheels.suspension(_ctx(dims, s), +1 if s == "Front" else -1), name)

    # --- reactor: authored core-local, main axis +Y ---
    if name.startswith(("LC_Reactor", "LC_Gyro")):
        rc = REACTOR_AT
        if name == "LC_Reactor_Core":
            bm = reactor.core()
        elif name.startswith("LC_Reactor_Ring_"):
            bm = reactor.ring("ABC".index(name[-1]))
        elif name.startswith("LC_Gyro_"):
            bm = reactor.gyro(name[-1].lower())
        elif name == "LC_Reactor_Housing":
            bm = reactor.housing()
        elif name == "LC_Reactor_Energy":
            bm = reactor.energy()
        else:
            return None
        bmesh.ops.translate(bm, verts=bm.verts[:], vec=rc)
        return bm

    if name == "LC_RearDrive":
        return place(wheels.rear_drive(_ctx(dims, "Rear")), "LC_Wheel_Rear")

    if name == "LC_SteeringYoke":
        return place(wheels.steering_yoke(_ctx(dims, "Front")), "LC_Wheel_Front")

    return None


def _names(name):  # kept for `handled()`
    return build_node(name, {"wheelOuterDiameter": 1, "wheelSectionWidth": 1,
                             "hubVoidDiameter": 1}, lambda _n: 0.0) is not None


build_node.__wrapped_names__ = _names
