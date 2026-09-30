#!/usr/bin/env python3
"""Build the canonical modular Light Cycle in Blender and export lightcycle.glb.

    blender --background --python tools/build_lightcycle.py

What this produces is the canonical production hierarchy: every contractual node
exists with the right parent, material, and physical pivot. Hard-surface builders
replace proxy geometry without touching names, so adapters, validation, animation,
and the manifest stay stable throughout production.

Verified against Blender 5.2.1 LTS. Socket names are the 5.x ones ('Coat Weight',
'Transmission Weight'); the 'Clearcoat *' names of older releases do not exist.
"""
import json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402 - real hard-surface builders, dispatched per node name

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())
NODES = json.loads((ROOT / "spec/lightcycle.nodes.json").read_text())["nodes"]
D = SPEC["dimensions_m"]
TEX_ROOT = ROOT / "assets/textures/generated"


def srgb_to_linear(hex_color: str) -> tuple:
    """Blender's Base Color socket is linear; the spec stores sRGB hex as authored."""
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)



def attach_texture_maps(mat, name: str, bsdf):
    """Attach deterministic neutral texture maps when the generated package exists.

    Scalars remain a safe fallback when somebody invokes Blender directly instead
    of npm run build:glb. Player hue is never sourced from these files.
    """
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    stem = name.lower()

    def tex(suffix: str, colorspace: str):
        path = TEX_ROOT / f"{stem}_{suffix}.png"
        if not path.exists():
            return None
        node = nodes.new("ShaderNodeTexImage")
        node.name = f"LC_{suffix}"
        node.label = suffix
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.image.colorspace_settings.name = colorspace
        node.extension = "REPEAT"
        return node

    if SPEC["materials"][name].get("emissive"):
        mask = tex("emissive_mask", "Non-Color")
        if mask:
            links.new(mask.outputs["Color"], bsdf.inputs["Emission Color"])
        return

    base = tex("basecolor", "sRGB")
    rough = tex("roughness", "Non-Color")
    metallic = tex("metallic", "Non-Color")
    normal = tex("normal", "Non-Color")

    if base:
        links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    if rough:
        links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    if metallic:
        links.new(metallic.outputs["Color"], bsdf.inputs["Metallic"])
    if normal:
        nm = nodes.new("ShaderNodeNormalMap")
        nm.name = "LC_NormalMap"
        nm.inputs["Strength"].default_value = 0.42
        links.new(normal.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])


def unwrap_production(objects):
    """Create stable UVs after the final production topology exists."""
    count = 0
    for o in objects.values():
        if o.type != "MESH" or o.get("lc_geometry") != "production":
            continue
        if not o.data.polygons:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.018)
        bpy.ops.object.mode_set(mode="OBJECT")
        o.select_set(False)
        count += 1
    print(f"UV unwrap: {count} production mesh nodes")


def build_materials() -> dict:
    mats = {}
    for name, m in SPEC["materials"].items():
        mat = bpy.data.materials.new(name)
        assert mat.name == name, f"material name collided: wanted {name}, got {mat.name}"
        mat.use_nodes = True
        b = mat.node_tree.nodes["Principled BSDF"]

        def put(socket, value):
            if socket in b.inputs:
                b.inputs[socket].default_value = value
            else:
                sys.exit(f"{name}: Principled has no socket {socket!r} in this Blender build")

        put("Base Color", srgb_to_linear(m["baseColor"]))
        put("Metallic", m.get("metallic", 0.0))
        put("Roughness", m.get("roughness", 0.5))
        put("IOR", m.get("ior", 1.5))
        put("Coat Weight", m.get("coat", 0.0))
        if m.get("coat"):
            put("Coat Roughness", m.get("coatRoughness", 0.03))
        put("Anisotropic", m.get("anisotropic", 0.0))
        # Blender stores rotation as a 0-1 turn fraction; the exporter converts to radians.
        put("Anisotropic Rotation", m.get("anisotropicRotation", 0.0))
        put("Transmission Weight", m.get("transmission", 0.0))

        if m.get("emissive"):
            # Neutral white emission only. Baking a player hue here would make the
            # six colours un-switchable at runtime, and validate_glb.py fails on it.
            put("Emission Color", srgb_to_linear(m["emissionColor"]))
            put("Emission Strength", m["emissionStrength"])
            mat["lc_mat_role"] = "emissive_mask"
            mat["lc_mask_channel"] = m["channel"]
        else:
            put("Emission Strength", 0.0)
            mat["lc_mat_role"] = "physical"

        mats[name] = mat
    return mats


# --- blockout placement -------------------------------------------------------
# Positions are derived from dimensions_m so the silhouette and the rider volume
# are right from the first export. Proxy shapes only; the modelling replaces them.
HALF_WB = D["wheelbase"] / 2
WHEEL_R = D["wheelOuterDiameter"] / 2
HUB_R = D["hubVoidDiameter"] / 2
AXLE_Z = WHEEL_R + D["groundClearance"] - WHEEL_R  # hub sits at wheel radius above ground
AXLE_Z = WHEEL_R


def wheel_x(name: str) -> float:
    return -HALF_WB if "Front" in name else HALF_WB


def placement(entry: dict):
    """-> (primitive, location, rotation_euler, size) for one blockout proxy."""
    n = entry["name"]
    half_w = D["width"] / 2

    if "_Wheel_" in n or n.endswith(("_BrakeDisc",)):
        x, z = wheel_x(n), AXLE_Z
        if n.endswith("_OuterRing"):
            return ("torus", (x, 0, z), (0, math.pi / 2, 0),
                    {"major": (WHEEL_R + HUB_R) / 2, "minor": (WHEEL_R - HUB_R) / 2})
        if n.endswith("_InnerRing"):
            return ("cyl", (x, 0, z), (0, math.pi / 2, 0),
                    {"r": HUB_R * 1.06, "d": D["wheelSectionWidth"] * 0.72})
        if n.endswith("_Bearing"):
            return ("cyl", (x, 0, z), (0, math.pi / 2, 0),
                    {"r": HUB_R * 0.94, "d": D["wheelSectionWidth"] * 0.55})
        if n.endswith("_EnergyRing"):
            return ("torus", (x, 0, z), (0, math.pi / 2, 0),
                    {"major": HUB_R * 1.12, "minor": 0.022})
        if n.endswith("_BrakeDisc"):
            return ("cyl", (x, 0, z), (0, math.pi / 2, 0), {"r": HUB_R * 0.8, "d": 0.012})

    if "_Caliper_" in n:
        y = half_w * 0.55 * (1 if n.endswith("_L") else -1)
        return ("cube", (wheel_x(n), y, AXLE_Z + HUB_R * 0.8), (0, 0, 0), {"s": (0.09, 0.03, 0.07)})
    if n.endswith("_Suspension"):
        return ("cube", (wheel_x(n) * 0.72, 0, AXLE_Z), (0, 0, 0), {"s": (0.34, 0.07, 0.07)})
    if n == "LC_SteeringYoke":
        return ("cube", (-HALF_WB * 0.62, 0, AXLE_Z + 0.09), (0, 0, 0), {"s": (0.12, 0.2, 0.05)})
    if n == "LC_RearDrive":
        return ("cyl", (HALF_WB * 0.66, 0, AXLE_Z - 0.04), (0, math.pi / 2, 0), {"r": 0.09, "d": 0.16})

    if n.startswith("LC_Reactor") or n.startswith("LC_Gyro"):
        rx, rz = 0.30, AXLE_Z - 0.06
        if n == "LC_Reactor_Core":
            return ("sphere", (rx, 0, rz), (0, 0, 0), {"r": 0.055})
        if n.startswith("LC_Reactor_Ring_"):
            k = {"A": 1.0, "B": 1.26, "C": 1.52}[n[-1]]
            return ("torus", (rx, 0, rz), (0, math.pi / 2, 0), {"major": 0.085 * k, "minor": 0.012})
        if n.startswith("LC_Gyro_"):
            ax = {"X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0), "Z": (0, 0, 0)}[n[-1]]
            return ("torus", (rx, 0, rz), ax, {"major": 0.165, "minor": 0.008})
        if n == "LC_Reactor_Housing":
            return ("cyl", (rx, 0, rz), (0, math.pi / 2, 0), {"r": 0.20, "d": 0.14})
        if n == "LC_Reactor_Energy":
            return ("torus", (rx, 0, rz), (0, math.pi / 2, 0), {"major": 0.19, "minor": 0.006})

    # Chassis, cockpit, canopy, emission strips, damage panels: laid along the deck.
    # Contact-point positions below were solved by tools/rider_proxy.py against a
    # 50th-percentile prone rider, not placed by eye. Re-run it after moving any
    # of them; an unreachable control is the fastest way to make a model look wrong.
    deck = {
        "LC_Body_Core": (0.0, 0, 0.50, (0.62, 0.17, 0.11)),
        "LC_Body_Spine": (0.0, 0, 0.60, (0.72, 0.07, 0.04)),
        "LC_Belly": (0.0, 0, 0.30, (0.60, 0.15, 0.07)),
        "LC_Underbody": (0.0, 0, 0.19, (0.68, 0.16, 0.03)),
        "LC_Nose_Shell_L": (-0.58, 1, 0.52, (0.34, 0.06, 0.12)),
        "LC_Nose_Shell_R": (-0.58, -1, 0.52, (0.34, 0.06, 0.12)),
        "LC_Mid_Shell_L": (0.0, 1, 0.50, (0.40, 0.05, 0.13)),
        "LC_Mid_Shell_R": (0.0, -1, 0.50, (0.40, 0.05, 0.13)),
        "LC_Rear_Shell_L": (0.60, 1, 0.52, (0.32, 0.06, 0.13)),
        "LC_Rear_Shell_R": (0.60, -1, 0.52, (0.32, 0.06, 0.13)),
        "LC_Armor_L": (0.18, 1, 0.42, (0.46, 0.03, 0.09)),
        "LC_Armor_R": (0.18, -1, 0.42, (0.46, 0.03, 0.09)),
        "LC_Handlebar_L": (-0.72, 1, 0.70, (0.06, 0.09, 0.03)),
        "LC_Handlebar_R": (-0.72, -1, 0.70, (0.06, 0.09, 0.03)),
        "LC_Control_L": (-0.78, 1, 0.70, (0.05, 0.04, 0.03)),
        "LC_Control_R": (-0.78, -1, 0.70, (0.05, 0.04, 0.03)),
        "LC_ChestSupport": (-0.238, 0, 0.528, (0.22, 0.14, 0.03)),
        "LC_ShinRest_L": (0.443, 1, 0.695, (0.20, 0.05, 0.06), 0.92),
        "LC_ShinRest_R": (0.443, -1, 0.695, (0.20, 0.05, 0.06), 0.92),
        "LC_FootRest_L": (0.620, 1, 0.280, (0.07, 0.05, 0.02), 0.92),
        "LC_FootRest_R": (0.620, -1, 0.280, (0.07, 0.05, 0.02), 0.92),
        "LC_RiderMount": (0.05, 0, 0.58, (0.30, 0.11, 0.02)),
        "LC_CockpitDisplay": (-0.52, 0, 0.66, (0.09, 0.10, 0.01)),
        "LC_Canopy_Center": (0.62, 0, 0.856, (0.26, 0.12, 0.04)),
        "LC_Canopy_L": (0.62, 1, 0.790, (0.26, 0.04, 0.12)),
        "LC_Canopy_R": (0.62, -1, 0.790, (0.26, 0.04, 0.12)),
        "LC_BackSupport": (0.44, 0, 0.72, (0.14, 0.13, 0.03)),
        "LC_DeployArm_L": (0.50, 1, 0.80, (0.18, 0.02, 0.02)),
        "LC_DeployArm_R": (0.50, -1, 0.80, (0.18, 0.02, 0.02)),
        "LC_CanopyEnergy": (0.62, 0, 0.896, (0.24, 0.10, 0.006)),
        "LC_Emit_BodyPrimary": (0.0, 1, 0.55, (0.66, 0.004, 0.018)),
        "LC_Emit_BodySecondary": (0.0, 1, 0.38, (0.52, 0.004, 0.008)),
        "LC_Emit_FrontWheel": (-0.80, 1, 0.55, (0.16, 0.004, 0.02)),
        "LC_Emit_RearWheel": (0.80, 1, 0.55, (0.16, 0.004, 0.02)),
        "LC_Emit_Reactor": (0.30, 1, 0.40, (0.10, 0.004, 0.012)),
        "LC_Emit_Cockpit": (-0.50, 0, 0.68, (0.07, 0.05, 0.004)),
        "LC_Emit_Rear": (0.86, 0, 0.60, (0.01, 0.13, 0.03)),
        "LC_Emit_TrailPort": (0.90, 0, 0.46, (0.01, 0.09, 0.05)),
        "LC_Damage_Nose_L": (-0.66, 1, 0.52, (0.18, 0.012, 0.10)),
        "LC_Damage_Nose_R": (-0.66, -1, 0.52, (0.18, 0.012, 0.10)),
        "LC_Damage_Panel_L1": (-0.16, 1, 0.50, (0.20, 0.012, 0.11)),
        "LC_Damage_Panel_L2": (0.16, 1, 0.50, (0.20, 0.012, 0.11)),
        "LC_Damage_Panel_R1": (-0.16, -1, 0.50, (0.20, 0.012, 0.11)),
        "LC_Damage_Panel_R2": (0.16, -1, 0.50, (0.20, 0.012, 0.11)),
        "LC_Damage_Rear_L": (0.72, 1, 0.52, (0.18, 0.012, 0.10)),
        "LC_Damage_Rear_R": (0.72, -1, 0.52, (0.18, 0.012, 0.10)),
        "LC_Damage_ReactorCover": (0.30, 1, 0.40, (0.17, 0.012, 0.17)),
    }
    if n in deck:
        entry = deck[n]
        x, yside, z, sc = entry[:4]
        yf = entry[4] if len(entry) > 4 else 0.86  # leg rests sit further outboard
        return ("cube", (x, yside * half_w * yf, z), (0, 0, 0), {"s": sc})
    return None


COL_PROXY = {
    "COL_LC_Body": ((0, 0, 0.50), (0.95, 0.24, 0.26)),
    "COL_LC_FrontWheel": ((-HALF_WB, 0, AXLE_Z), (WHEEL_R, D["wheelSectionWidth"] / 2, WHEEL_R)),
    "COL_LC_RearWheel": ((HALF_WB, 0, AXLE_Z), (WHEEL_R, D["wheelSectionWidth"] / 2, WHEEL_R)),
    "COL_LC_RiderZone": ((0.05, 0, 0.70), (0.55, 0.20, 0.16)),
}

def production_pivot(name: str):
    """World-space origin for nodes animated directly rather than through a parent.

    Production bmeshes are authored in world coordinates. Without moving the mesh
    data back around the physical pivot and placing the object origin there, a
    perfectly named reactor ring or canopy panel rotates around world (0,0,0).
    """
    half_w = D["width"] / 2
    if name == "LC_Reactor_Core" or name.startswith(("LC_Reactor_Ring_", "LC_Gyro_")):
        return (0.30, 0.0, AXLE_Z - 0.06)
    if name.startswith("LC_Canopy_") and name in {"LC_Canopy_L", "LC_Canopy_R"}:
        side = 1 if name.endswith("_L") else -1
        y = side * half_w * 0.86 * 0.62
        return (0.62, y, 0.755)
    if name.startswith("LC_DeployArm_"):
        side = 1 if name.endswith("_L") else -1
        y = side * half_w * 0.73 * 0.72
        return (0.44, y, 0.735)
    damage = {
        "LC_Damage_Nose_L": (-0.655, half_w * 0.86 * 1.10, 0.50),
        "LC_Damage_Nose_R": (-0.655, -half_w * 0.86 * 1.10, 0.50),
        "LC_Damage_Panel_L1": (-0.155, half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_Panel_L2": (0.155, half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_Panel_R1": (-0.155, -half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_Panel_R2": (0.155, -half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_Rear_L": (0.610, half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_Rear_R": (0.610, -half_w * 0.86 * 1.10, 0.49),
        "LC_Damage_ReactorCover": (0.30, half_w * 0.82, 0.40),
    }
    return damage.get(name)


def set_mesh_origin_world(obj, pivot):
    """Move an object's origin to a world pivot without moving visible geometry."""
    if pivot is None or obj.type != "MESH":
        return
    p = Vector(pivot)
    for v in obj.data.vertices:
        v.co -= p
    obj.location = p


EMPTY_AT = {
    # Pivots that must sit on real hardware, not the world origin: wheel spin
    # happens about the axle and the reactor rings counter-rotate about the core.
    "LC_Wheel_Front": (-HALF_WB, 0, AXLE_Z), "LC_Wheel_Rear": (HALF_WB, 0, AXLE_Z),
    "LC_Reactor": (0.30, 0, AXLE_Z - 0.06),
    "LC_FX_TrailOrigin": (0.92, 0, 0.46), "LC_FX_Boost": (0.95, 0, 0.55),
    "LC_FX_Reactor": (0.30, 0, 0.44), "LC_FX_FrontWheel": (-HALF_WB, 0, AXLE_Z),
    "LC_FX_RearWheel": (HALF_WB, 0, AXLE_Z),
    "LC_FX_Spark_FL": (-HALF_WB, 0.14, 0.06), "LC_FX_Spark_FR": (-HALF_WB, -0.14, 0.06),
    "LC_FX_Spark_RL": (HALF_WB, 0.14, 0.06), "LC_FX_Spark_RR": (HALF_WB, -0.14, 0.06),
    "LC_FX_CrashCenter": (0, 0, 0.50), "LC_FX_DerezCenter": (0.10, 0, 0.55),
    "LC_FX_Impact_L": (0, 0.22, 0.50), "LC_FX_Impact_R": (0, -0.22, 0.50),
}


def make_mesh(entry, mats):
    n = entry["name"]

    # Production geometry first; anything without a builder keeps its proxy.
    if entry["kind"] == "mesh":
        bm = geo.build_node(n, D, wheel_x)
        if bm is not None:
            o = geo.L.obj_from_bm(bm, n)
            o.data.shade_smooth()
            geo.L.bevel_obj(o, width=0.0022, segments=2, angle_deg=32.0)
            set_mesh_origin_world(o, production_pivot(n))
            o["lc_geometry"] = "production"
            return o

    if entry["kind"] == "proxy":
        loc, s = COL_PROXY[n]
        bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
        o = bpy.context.object
        o.scale = s
        o.display_type = "WIRE"
        o.hide_render = True
        o["lc_role"] = "collision_proxy"
        return o

    p = placement(entry)
    if p is None:
        bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0, 0, 0.5))
        return bpy.context.object
    kind, loc, rot, a = p
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2, location=loc, rotation=rot)
        bpy.context.object.scale = a["s"]
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=a["r"], depth=a["d"],
                                            location=loc, rotation=rot)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=a["r"], location=loc)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=16,
                                         major_radius=a["major"], minor_radius=a["minor"],
                                         location=loc, rotation=rot)
    return bpy.context.object


def build():
    reset_scene()
    mats = build_materials()
    made = {}

    for entry in NODES:
        n, kind = entry["name"], entry["kind"]
        if kind == "empty":
            bpy.ops.object.empty_add(type="PLAIN_AXES", radius=0.04,
                                     location=EMPTY_AT.get(n, (0, 0, 0)))
            o = bpy.context.object
        else:
            o = make_mesh(entry, mats)
            if entry.get("mat") and not o.data.materials:
                o.data.materials.append(mats[entry["mat"]])
            o.data.name = f"{n}_MESH"
            if o.get("lc_geometry") != "production":
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.shade_smooth()

        # Blender renames on collision at assignment time, so a silent '.001' here
        # would break the node contract downstream. Fail loudly instead.
        o.name = n
        if o.name != n:
            sys.exit(f"node name collision: wanted {n!r}, Blender gave {o.name!r}")

        o["lc_kind"] = kind
        if entry.get("required"):
            o["lc_required"] = True
        if entry.get("spin"):
            o["lc_spin_axis"] = entry["spin"]
        if entry.get("detachable"):
            o["lc_detachable"] = True
        made[n] = o

    # Parent with keep_transform so the blockout placement survives, then move the
    # wheel pivots onto the axle - wheel spin is worthless around the world origin.
    for entry in NODES:
        if entry["parent"]:
            made[entry["name"]].parent = made[entry["parent"]]
            made[entry["name"]].matrix_parent_inverse = made[entry["parent"]].matrix_world.inverted()

    bpy.context.view_layer.update()
    unwrap_production(made)
    bpy.context.view_layer.update()
    prod = sum(1 for o in made.values() if o.get("lc_geometry") == "production")
    tris = sum(len(o.data.loop_triangles) for o in made.values()
               if o.type == "MESH" and (o.data.calc_loop_triangles() or True))
    print(f"production geometry: {prod} nodes | proxy: "
          f"{sum(1 for o in made.values() if o.type == 'MESH') - prod}")
    return made, tris


AXIS = {"x": 0, "y": 1, "z": 2}

# (object, clip) -> Action. A clip can drive several channels on several objects,
# so keys accumulate into one Action per pair before anything is pushed to NLA.
_ACTIONS = {}


def key(obj, track: str, path: str, index: int, frames, interp="BEZIER"):
    """Keyframe one channel of one object into the Action for `track`.

    The clip name lives on the NLA TRACK, never the Action: a clip like
    LC_Brake drives several objects and Blender refuses two Actions the same
    name. export_merge_animation='NLA_TRACK' folds same-named tracks into one
    glTF animation.
    """
    obj.rotation_mode = "XYZ"
    k = (obj.name, track)
    act = _ACTIONS.get(k)
    if act is None:
        act = bpy.data.actions.new(f"{track}__{obj.name}")
        _ACTIONS[k] = act
    obj.animation_data_create()
    obj.animation_data.action = act
    base = {"location": obj.location, "rotation_euler": obj.rotation_euler,
            "scale": obj.scale}[path]
    rest = base[index]
    for f, v in frames:
        base[index] = rest + v if path != "scale" else v
        obj.keyframe_insert(path, index=index, frame=f)
    base[index] = rest
    # Blender 5.x actions are slotted: fcurves live under layers -> strips ->
    # channelbags and Action.fcurves no longer exists.
    for layer in act.layers:
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = interp
    obj.animation_data.action = None


def spin(obj, track, turns, frames, axis="y"):
    key(obj, track, "rotation_euler", AXIS[axis],
        [(1, 0.0), (frames, turns * 2 * math.pi)], interp="LINEAR")


def push_tracks():
    """One NLA track per clip, named for the clip."""
    for (obj_name, track), act in _ACTIONS.items():
        obj = bpy.data.objects[obj_name]
        nla = obj.animation_data.nla_tracks.new()
        nla.name = track
        nla.strips.new(track, 1, act)


def author_clips(made: dict):
    """All 18 declared clips, driven by real pivots.

    Nothing here scales the bike or fakes motion with a morph - the doc forbids
    it and the modular hierarchy exists precisely so it is not needed.
    """
    M = made
    wheels = [M["LC_Wheel_Front"], M["LC_Wheel_Rear"]]
    rings = [(M["LC_Reactor_Ring_A"], 0.50), (M["LC_Reactor_Ring_B"], -0.34),
             (M["LC_Reactor_Ring_C"], 0.22)]
    gyros = [(M["LC_Gyro_X"], "x"), (M["LC_Gyro_Y"], "y"), (M["LC_Gyro_Z"], "z")]
    root, yoke = M["LC_ROOT"], M["LC_SteeringYoke"]
    susp = [M["LC_Wheel_Front_Suspension"], M["LC_Wheel_Rear_Suspension"]]

    # --- locomotion -------------------------------------------------------
    for w in wheels:
        spin(w, "LC_WheelSpin", 1.0, 48)
    for r, t in rings:
        spin(r, "LC_ReactorIdle", t, 96)
    for g, ax in gyros:
        spin(g, "LC_ReactorIdle", 0.25, 96, axis=ax)
    for r, t in rings:
        spin(r, "LC_ReactorAcceleration", t * 3.2, 48)
    for g, ax in gyros:
        spin(g, "LC_ReactorAcceleration", 0.9, 48, axis=ax)

    # Idle: the machine is never dead still - slow gyros and a breathing core.
    for g, ax in gyros:
        spin(g, "LC_Idle", 0.06, 120, axis=ax)
    key(M["LC_Reactor_Core"], "LC_Idle", "scale", 0,
        [(1, 1.0), (60, 1.015), (120, 1.0)])

    # --- steering and lean ------------------------------------------------
    for name, ang in (("LC_SteerLeft", 0.42), ("LC_SteerRight", -0.42)):
        key(yoke, name, "rotation_euler", AXIS["z"], [(1, 0.0), (12, ang), (24, ang)])
    for name, ang in (("LC_LeanLeft", 0.50), ("LC_LeanRight", -0.50)):
        key(root, name, "rotation_euler", AXIS["x"], [(1, 0.0), (14, ang), (28, ang)])

    # --- braking: real suspension travel, nose dives ----------------------
    for sp in susp:
        key(sp, "LC_Brake", "location", 2, [(1, 0.0), (8, -0.028), (20, -0.018), (30, 0.0)])
    key(root, "LC_Brake", "rotation_euler", AXIS["y"], [(1, 0.0), (9, -0.055), (30, 0.0)])

    # --- boost ------------------------------------------------------------
    for r, t in rings:
        spin(r, "LC_BoostEnter", t * 1.8, 18)
        spin(r, "LC_BoostLoop", t * 5.0, 24)
        spin(r, "LC_BoostExit", t * 1.4, 22)
    key(M["LC_Reactor_Core"], "LC_BoostEnter", "scale", 0, [(1, 1.0), (18, 1.22)])
    key(M["LC_Reactor_Core"], "LC_BoostLoop", "scale", 0,
        [(1, 1.22), (12, 1.30), (24, 1.22)])
    key(M["LC_Reactor_Core"], "LC_BoostExit", "scale", 0, [(1, 1.22), (22, 1.0)])

    # --- high-speed transformation: real hinges, no global scale ----------
    for nm, sgn in (("LC_Canopy_L", 1), ("LC_Canopy_R", -1)):
        key(M[nm], "LC_HighSpeedTransform", "rotation_euler", AXIS["x"],
            [(1, 0.0), (36, -1.15 * sgn)])
        key(M[nm], "LC_HighSpeedReverse", "rotation_euler", AXIS["x"],
            [(1, -1.15 * sgn), (30, 0.0)])
    for nm, sgn in (("LC_DeployArm_L", 1), ("LC_DeployArm_R", -1)):
        key(M[nm], "LC_HighSpeedTransform", "rotation_euler", AXIS["y"],
            [(1, 0.0), (36, 0.62 * sgn)])
        key(M[nm], "LC_HighSpeedReverse", "rotation_euler", AXIS["y"],
            [(1, 0.62 * sgn), (30, 0.0)])
    # The canopy assembly slides forward over the rider as it closes.
    key(M["LC_RearCanopy"], "LC_HighSpeedTransform", "location", 0,
        [(1, 0.0), (36, -0.115)])
    key(M["LC_RearCanopy"], "LC_HighSpeedReverse", "location", 0,
        [(1, -0.115), (30, 0.0)])

    # --- failure states ---------------------------------------------------
    for r, t in rings:
        spin(r, "LC_ReactorOverload", t * 7.0, 30)
    key(M["LC_Reactor_Core"], "LC_ReactorOverload", "scale", 0,
        [(1, 1.0), (10, 1.5), (16, 1.1), (24, 1.7), (30, 0.9)], interp="LINEAR")

    for nm in ("LC_Damage_Panel_L1", "LC_Damage_Panel_R2", "LC_Damage_Nose_L"):
        key(M[nm], "LC_Damage", "rotation_euler", AXIS["y"],
            [(1, 0.0), (10, 0.22), (26, 0.16)])
        key(M[nm], "LC_Damage", "location", 2, [(1, 0.0), (10, 0.012), (26, 0.008)])
    for r, t in rings:
        spin(r, "LC_Damage", t * 0.4, 26)

    key(root, "LC_Crash", "rotation_euler", AXIS["x"], [(1, 0.0), (12, 0.9), (34, 1.55)])
    key(root, "LC_Crash", "location", 2, [(1, 0.0), (8, 0.14), (34, -0.05)])
    for sp in susp:
        key(sp, "LC_Crash", "location", 2, [(1, 0.0), (10, -0.035), (34, -0.02)])

    # Derez: panels blow outward, the core collapses. The shader dissolve is a
    # runtime effect; this is only the mechanical part.
    for i, nm in enumerate(("LC_Damage_Nose_L", "LC_Damage_Nose_R", "LC_Damage_Panel_L1",
                            "LC_Damage_Panel_L2", "LC_Damage_Panel_R1", "LC_Damage_Panel_R2",
                            "LC_Damage_Rear_L", "LC_Damage_Rear_R", "LC_Damage_ReactorCover")):
        d = 0.16 + 0.03 * i
        key(M[nm], "LC_Derez", "location", 1, [(1, 0.0), (30, d * (1 if i % 2 else -1))])
        key(M[nm], "LC_Derez", "location", 2, [(1, 0.0), (30, 0.10 + 0.02 * i)])
        key(M[nm], "LC_Derez", "rotation_euler", AXIS["y"], [(1, 0.0), (30, 1.1 + 0.2 * i)])
    key(M["LC_Reactor_Core"], "LC_Derez", "scale", 0, [(1, 1.0), (14, 1.6), (30, 0.02)])

    push_tracks()


def export(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_extras=True,          # carries lc_* tags into node/material extras
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_merge_animation="NLA_TRACK",  # one glTF clip per track name, not per Action
        export_nla_strips=True,
        export_apply=True,           # bake production bevels into runtime geometry
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_gpu_instances=False,
        use_selection=False,
        use_visible=False,
        use_renderable=False,
    )


if __name__ == "__main__":
    made, tris = build()
    author_clips(made)
    blend = ROOT / "assets/source/lightcycle_blockout.blend"
    blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    out = ROOT / "assets/export/lightcycle.glb"
    export(out)
    print(f"\nBUILD OK  objects={len(made)}  tris={tris}  -> {out}")
