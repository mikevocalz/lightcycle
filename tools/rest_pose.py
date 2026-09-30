"""Persist and restore the neutral authoring pose without deleting clip actions.

NLA tracks are a clip library, not a scene-wide simultaneous animation stack.
Several exit/steer clips intentionally start displaced, so frame 1 is not rest.
"""
from mathutils import Matrix

REST_KEY = "lc_rest_matrix"


def capture_rest_pose(objects):
    """Record local basis matrices before any animation is authored/evaluated."""
    for obj in objects:
        obj[REST_KEY] = [value for row in obj.matrix_basis for value in row]


def restore_rest_pose(objects, require_recorded=True):
    """Disable live NLA evaluation and explicitly restore captured transforms.

    Blender retains the last evaluated transforms after NLA is disabled, so both
    steps are required. Keep tracks, strips and actions intact and unmuted: the
    glTF ACTIONS exporter still discovers all single-strip named tracks while
    animation_data.use_nla is False.
    """
    objects = list(objects)
    missing = [obj.name for obj in objects if REST_KEY not in obj]
    if missing and require_recorded:
        raise RuntimeError(
            "Rest pose metadata missing; rebuild the source before QA/export: "
            + ", ".join(missing[:8])
        )
    for obj in objects:
        if REST_KEY not in obj:
            continue
        if obj.animation_data:
            obj.animation_data.action = None
            obj.animation_data.use_nla = False
        values = list(obj[REST_KEY])
        if len(values) != 16:
            raise RuntimeError(f"Invalid recorded rest matrix on {obj.name}")
        obj.matrix_basis = Matrix([values[i:i + 4] for i in range(0, 16, 4)])
    return {
        "mode": "recorded_local_rest_matrices",
        "metadata_key": REST_KEY,
        "restored_count": len(objects) - len(missing),
        "restored_nodes": [obj.name for obj in objects if REST_KEY in obj],
        "nla_evaluation": "disabled",
        "actions_preserved": True,
    }
