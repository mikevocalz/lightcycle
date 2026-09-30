"""Real hard-surface geometry, dispatched per node name.

Nodes with a builder here get production geometry; nodes without one keep their
blockout proxy. That lets the model be finished assembly by assembly while the
node contract, the validator, the manifest and both runtime adapters keep
working the whole way through - which is the point of the modular hierarchy.
"""
from . import _lib as L
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


def build_node(name: str, dims: dict, x_of):
    """Return a bmesh for `name`, or None to fall back to the blockout proxy.

    `x_of(name)` gives the axle X for whichever end this node belongs to.
    """
    for suffix, fn in _WHEEL.items():
        if name.endswith(suffix) and "_Wheel_" in name:
            return fn(_ctx(dims, _side_of(name)), x_of(name))

    if "_Caliper_" in name:
        side = 1 if name.endswith("_L") else -1
        return wheels.caliper(_ctx(dims, _side_of(name)), x_of(name), side)

    if name.endswith("_Suspension"):
        s = _side_of(name)
        # The arm reaches inboard toward the chassis, so it points the other way
        # at each end.
        return wheels.suspension(_ctx(dims, s), x_of(name), +1 if s == "Front" else -1)

    if name == "LC_RearDrive":
        return wheels.rear_drive(_ctx(dims, "Rear"), x_of("LC_Wheel_Rear"))

    if name == "LC_SteeringYoke":
        return wheels.steering_yoke(_ctx(dims, "Front"), x_of("LC_Wheel_Front"))

    return None


def _names(name):  # kept for `handled()`
    return build_node(name, {"wheelOuterDiameter": 1, "wheelSectionWidth": 1,
                             "hubVoidDiameter": 1}, lambda _n: 0.0) is not None


build_node.__wrapped_names__ = _names
