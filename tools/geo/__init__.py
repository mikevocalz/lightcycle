"""Real hard-surface geometry, dispatched per node name.

Nodes with a builder here get production geometry; nodes without one keep their
blockout proxy. This lets the asset migrate assembly-by-assembly without
renaming contractual nodes or breaking runtime adapters.
"""
import bmesh

from . import _lib as L
from . import chassis
from . import cockpit
from . import damage
from . import emission
from . import reactor
from . import wheels

__all__ = ["build_node", "handled", "L"]


def _ctx(dims, side):
    """Geometry parameters for one wheel end."""
    return {
        "R": dims["wheelOuterDiameter"] / 2,
        "hw": dims.get("frontWheelSectionWidth" if side == "Front" else "rearWheelSectionWidth",
                       dims["wheelSectionWidth"]) / 2,
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

_CHASSIS_NAMES = {
    "LC_Body_Core", "LC_Body_Spine", "LC_Belly", "LC_Underbody",
    "LC_Nose_Shell_L", "LC_Nose_Shell_R", "LC_Mid_Shell_L", "LC_Mid_Shell_R",
    "LC_Rear_Shell_L", "LC_Rear_Shell_R", "LC_Armor_L", "LC_Armor_R",
}

_COCKPIT_NAMES = {
    "LC_Handlebar_L", "LC_Handlebar_R", "LC_Control_L", "LC_Control_R",
    "LC_ChestSupport", "LC_ShinRest_L", "LC_ShinRest_R",
    "LC_FootRest_L", "LC_FootRest_R", "LC_RiderMount", "LC_CockpitDisplay",
    "LC_Canopy_Center", "LC_Canopy_L", "LC_Canopy_R", "LC_BackSupport",
    "LC_DeployArm_L", "LC_DeployArm_R", "LC_CanopyEnergy",
}

_DAMAGE_NAMES = {
    "LC_Damage_Nose_L", "LC_Damage_Nose_R",
    "LC_Damage_Panel_L1", "LC_Damage_Panel_L2",
    "LC_Damage_Panel_R1", "LC_Damage_Panel_R2",
    "LC_Damage_Rear_L", "LC_Damage_Rear_R", "LC_Damage_ReactorCover",
}

_EMISSION_NAMES = {
    "LC_Emit_BodyPrimary", "LC_Emit_BodySecondary",
    "LC_Emit_FrontWheel", "LC_Emit_RearWheel", "LC_Emit_Reactor",
    "LC_Emit_Cockpit", "LC_Emit_Rear", "LC_Emit_TrailPort",
}


def handled(name: str) -> bool:
    if name in _CHASSIS_NAMES | _COCKPIT_NAMES | _DAMAGE_NAMES | _EMISSION_NAMES:
        return True
    if name == "LC_RearDrive" or name == "LC_SteeringYoke":
        return True
    if name.startswith(("LC_Reactor", "LC_Gyro")):
        return True
    return (
        any(name.endswith(suffix) and "_Wheel_" in name for suffix in _WHEEL)
        or "_Caliper_" in name
        or name.endswith("_Suspension")
    )


# Legacy fallback only. Current builds derive the reactor centre from dimensions_m.
REACTOR_AT = (0.30, 0.0, 0.40)


def _lift(bm, x, dz):
    """Move an axle-local shell onto its real axle."""
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(x, 0.0, dz))
    return bm


def build_node(name: str, dims: dict, x_of):
    """Return a bmesh for `name`, or None to fall back to the blockout proxy."""
    axle_z = dims["wheelOuterDiameter"] / 2

    def place(bm, name_for_x):
        return _lift(bm, x_of(name_for_x), axle_z)

    # --- chassis ----------------------------------------------------------
    if name == "LC_Body_Core":
        return chassis.build_body_core(dims)
    if name == "LC_Body_Spine":
        return chassis.build_body_spine(dims)
    if name == "LC_Belly":
        return chassis.build_belly(dims)
    if name == "LC_Underbody":
        return chassis.build_underbody(dims)
    if name.startswith("LC_Nose_Shell_"):
        return chassis.nose_shell(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_Mid_Shell_"):
        return chassis.mid_shell(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_Rear_Shell_"):
        return chassis.rear_shell(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_Armor_"):
        return chassis.armor(dims, 1 if name.endswith("_L") else -1)

    # --- cockpit / canopy -------------------------------------------------
    if name.startswith("LC_Handlebar_"):
        return cockpit.handlebar(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_Control_"):
        return cockpit.control(dims, 1 if name.endswith("_L") else -1)
    if name == "LC_ChestSupport":
        return cockpit.chest_support(dims)
    if name.startswith("LC_ShinRest_"):
        return cockpit.shin_rest(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_FootRest_"):
        return cockpit.foot_rest(dims, 1 if name.endswith("_L") else -1)
    if name == "LC_RiderMount":
        return cockpit.rider_mount(dims)
    if name == "LC_CockpitDisplay":
        return cockpit.cockpit_display(dims)
    if name == "LC_Canopy_Center":
        return cockpit.canopy_center(dims)
    if name.startswith("LC_Canopy_") and name != "LC_CanopyEnergy":
        return cockpit.canopy_side(dims, 1 if name.endswith("_L") else -1)
    if name == "LC_BackSupport":
        return cockpit.back_support(dims)
    if name.startswith("LC_DeployArm_"):
        return cockpit.deploy_arm(dims, 1 if name.endswith("_L") else -1)
    if name == "LC_CanopyEnergy":
        return cockpit.canopy_energy(dims)

    # --- emission inserts -------------------------------------------------
    if name == "LC_Emit_BodyPrimary":
        return emission.body_primary(dims)
    if name == "LC_Emit_BodySecondary":
        return emission.body_secondary(dims)
    if name == "LC_Emit_FrontWheel":
        return emission.wheel_marker(dims, True)
    if name == "LC_Emit_RearWheel":
        return emission.wheel_marker(dims, False)
    if name == "LC_Emit_Reactor":
        return emission.reactor(dims)
    if name == "LC_Emit_Cockpit":
        return emission.cockpit(dims)
    if name == "LC_Emit_Rear":
        return emission.rear(dims)
    if name == "LC_Emit_TrailPort":
        return emission.trail_port(dims)

    # --- damage skins -----------------------------------------------------
    if name.startswith("LC_Damage_Nose_"):
        return damage.nose(dims, 1 if name.endswith("_L") else -1)
    if name.startswith("LC_Damage_Panel_L"):
        return damage.mid(dims, 1, int(name[-1]))
    if name.startswith("LC_Damage_Panel_R"):
        return damage.mid(dims, -1, int(name[-1]))
    if name.startswith("LC_Damage_Rear_"):
        return damage.rear(dims, 1 if name.endswith("_L") else -1)
    if name == "LC_Damage_ReactorCover":
        return damage.reactor_cover(dims)

    # --- wheels -----------------------------------------------------------
    for suffix, fn in _WHEEL.items():
        if name.endswith(suffix) and "_Wheel_" in name:
            return place(fn(_ctx(dims, _side_of(name))), name)

    if "_Caliper_" in name:
        return place(wheels.caliper(_ctx(dims, _side_of(name)), 1 if name.endswith("_L") else -1), name)

    if name.endswith("_Suspension"):
        s = _side_of(name)
        return place(wheels.suspension(_ctx(dims, s), +1 if s == "Front" else -1), name)

    # --- reactor ----------------------------------------------------------
    if name.startswith(("LC_Reactor", "LC_Gyro")):
        rc = (dims.get("reactorCenterX", REACTOR_AT[0]), 0.0,
              dims.get("reactorCenterZ", REACTOR_AT[2]))
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
