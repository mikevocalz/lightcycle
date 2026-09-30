#!/usr/bin/env python3
"""Validate an exported lightcycle GLB against spec/, and emit its manifest.

Parses the GLB's JSON chunk directly - no Blender, no npm, no deps - so it runs
in CI on a bare runner. Exit 1 on any contract breach.

    tools/validate_glb.py assets/export/lightcycle.glb --manifest assets/export/manifest.json
"""
import argparse, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_glb_json(path: Path) -> dict:
    data = path.read_bytes()
    magic, version, _length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        sys.exit(f"{path}: not a GLB (magic was {magic!r})")
    if version != 2:
        sys.exit(f"{path}: glTF version {version}, expected 2")
    off = 12
    while off < len(data):
        clen, ctype = struct.unpack_from("<I4s", data, off)
        if ctype == b"JSON":
            return json.loads(data[off + 8 : off + 8 + clen])
        off += 8 + clen + (-clen % 4)
    sys.exit(f"{path}: no JSON chunk")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("glb", type=Path)
    ap.add_argument("--manifest", type=Path, help="write a node/material/clip manifest here")
    args = ap.parse_args()

    spec = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())
    nodespec = json.loads((ROOT / "spec/lightcycle.nodes.json").read_text())
    g = read_glb_json(args.glb)

    node_names = [n.get("name", "") for n in g.get("nodes", [])]
    mat_names = [m.get("name", "") for m in g.get("materials", [])]
    clip_names = [a.get("name", "") for a in g.get("animations", [])]
    errors, warnings = [], []

    # 1. Contractual nodes. These are named in HANDOFF.md as must-not-lose; a
    #    rename here silently breaks every adapter, so it is an error not a warning.
    required = [n["name"] for n in nodespec["nodes"] if n.get("required")]
    missing = [n for n in required if n not in node_names]
    if missing:
        errors.append(f"required nodes missing or renamed: {missing}")

    # 2. Full hierarchy. Losing a non-required node is recoverable, so warn.
    declared = [n["name"] for n in nodespec["nodes"]]
    absent = [n for n in declared if n not in node_names and n not in missing]
    if absent:
        warnings.append(f"{len(absent)} spec'd nodes absent (not yet modelled?): {absent[:8]}...")

    # 3. Parenting. A correct name on the wrong parent breaks pivots.
    idx = {i: n for i, n in enumerate(g.get("nodes", []))}
    parent_of = {c: n.get("name", "") for n in g.get("nodes", []) for c in n.get("children", [])}
    for entry in nodespec["nodes"]:
        if not entry["parent"] or entry["name"] not in node_names:
            continue
        i = node_names.index(entry["name"])
        actual = parent_of.get(i)
        if actual is not None and actual != entry["parent"]:
            errors.append(f"{entry['name']}: parent is {actual!r}, spec says {entry['parent']!r}")

    # 4. Materials. Exact set - an extra material means a stray, a missing one
    #    means a mesh silently fell back to a default.
    for m in spec["materials"]:
        if m not in mat_names:
            warnings.append(f"material {m} not in GLB")
    for m in mat_names:
        if m and m not in spec["materials"]:
            errors.append(f"unspec'd material in GLB: {m!r} (bake nothing outside the spec)")

    # 5. No baked player hue. The emissive masks must be neutral; a colored
    #    emissiveFactor means someone baked a color in and runtime switching dies.
    for m in g.get("materials", []):
        ef = m.get("emissiveFactor")
        if ef and max(ef) > 0 and (max(ef) - min(ef)) > 0.02:
            errors.append(f"{m.get('name')}: emissiveFactor {ef} is not neutral - player hue is baked in")

    # 6. Clips.
    for c in spec["clips"]:
        if c not in clip_names:
            warnings.append(f"clip {c} not in GLB")
    for c in clip_names:
        if c and c not in spec["clips"]:
            errors.append(f"unspec'd animation clip: {c!r}")

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps({
            "source": str(args.glb),
            "specVersion": spec["specVersion"],
            "nodes": node_names,
            "materials": mat_names,
            "clips": clip_names,
            "meshCount": len(g.get("meshes", [])),
            "primitiveCount": sum(len(m.get("primitives", [])) for m in g.get("meshes", [])),
            "triangles": None,  # filled by the Blender exporter, not derivable from JSON alone
        }, indent=1))
        print(f"manifest -> {args.manifest}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(node_names)} nodes, {len(mat_names)} materials, {len(clip_names)} clips, "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
