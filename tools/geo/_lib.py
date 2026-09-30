"""Hard-surface helpers for procedural Light Cycle geometry.

Everything here builds real topology - revolved profiles, radial arrays, bevelled
edges - rather than scaled primitives. The point is that the asset reads as
machined with every emissive switched off, and the thing that sells that is edge
highlights catching light, which needs actual bevels and actual panel breaks.

Bike length is +X, lateral is +Y, up is +Z in Blender; wheel/reactor spin axis is +Y.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

TAU = 6.283185307179586

# Which world axis each spin axis uses, and how (lateral, radius) map onto it.
AXES = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
LATERAL = AXES
RADIAL = {"x": (0.0, 0.0, 1.0), "y": (0.0, 0.0, 1.0), "z": (1.0, 0.0, 0.0)}


def new_bm() -> bmesh.types.BMesh:
    return bmesh.new()


def obj_from_bm(bm: bmesh.types.BMesh, name: str, mat=None):
    me = bpy.data.meshes.new(f"{name}_MESH")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def revolve(bm, profile, segments=64, axis="y", center=(0, 0, 0), closed=True):
    """Spin a closed (lateral, radius) profile about `axis` into a solid ring.

    The lateral component lies ALONG the spin axis and the radius in the plane
    perpendicular to it. Putting lateral anywhere else folds it into the rotation
    radius and the ring collapses to a ribbon - that bug cost a rebuild once.

    Wheels spin about the LATERAL axis of the bike, which is Y in Blender space
    (length X, up Z). Spinning them about X mounts the wheel sideways.
    """
    ax = AXES[axis]
    lat, rad = LATERAL[axis], RADIAL[axis]
    verts = []
    for y, z in profile:
        v = Vector(center) + Vector(lat) * y + Vector(rad) * z
        verts.append(bm.verts.new(v))
    edges = []
    n = len(verts)
    for i in range(n if closed else n - 1):
        edges.append(bm.edges.new((verts[i], verts[(i + 1) % n])))
    bmesh.ops.spin(bm, geom=edges, cent=center, axis=ax, angle=TAU,
                   steps=segments, use_merge=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def radial(bm, build, count, radius, axis="y", along=0.0, phase=0.0):
    """Stamp `build(bm, matrix)` count times around `axis` at `radius`.

    Bolt circles, cooling slots, brake vanes and bearing rollers are all this.
    Real geometry rather than a normal-map detail is what holds up in the wheel
    and reactor macro shots the QA matrix calls for.
    """
    lat, rad = Vector(LATERAL[axis]), Vector(RADIAL[axis])
    tan = Vector(AXES[axis]).cross(rad)
    rot_axis = {"x": "X", "y": "Y", "z": "Z"}[axis]
    for i in range(count):
        a = phase + TAU * i / count
        loc = lat * along + rad * (radius * math.cos(a)) + tan * (radius * math.sin(a))
        build(bm, Matrix.Translation(loc) @ Matrix.Rotation(a, 4, rot_axis))
    return bm


def box(bm, mat, size):
    """Axis-aligned box placed by matrix. size is full extents."""
    sx, sy, sz = (s / 2 for s in size)
    ret = bmesh.ops.create_cube(bm, size=1, matrix=mat @ Matrix.Diagonal((sx * 2, sy * 2, sz * 2, 1)))
    return ret


def cylinder(bm, mat, radius, depth, segments=24, cap=True):
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth, matrix=mat)
    return bm


def bevel_obj(ob, width=0.003, segments=2, angle_deg=35.0):
    """Bevel by angle so only real corners catch a highlight.

    This single modifier does more for the lights-off read than any texture -
    a perfectly sharp CG edge is the tell that something is not a machined part.
    """
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width, m.segments = width, segments
    m.limit_method = "ANGLE"
    m.angle_limit = angle_deg * 3.141592653589793 / 180
    m.harden_normals = True
    m.miter_outer = "MITER_ARC"
    return m


def shade_smooth(ob, angle_deg=40.0):
    ob.data.shade_smooth()
    ob.data.use_auto_smooth = True if hasattr(ob.data, "use_auto_smooth") else False
    m = ob.modifiers.new("Smooth", "WEIGHTED_NORMAL") if "WEIGHTED_NORMAL" else None
    return ob


def tri_count(ob) -> int:
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)
