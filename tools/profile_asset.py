#!/usr/bin/env python3
"""Static asset-budget report for canonical and LOD GLBs.

This is not a claim about headset FPS. It verifies file size, nodes/materials,
animations, and triangle counts so hardware profiling starts from an admitted
asset rather than a mystery build.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/export/performance.json"


def read_glb(path: Path):
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError(f"{path} is not glTF 2 GLB")
    off = 12
    while off < len(data):
        n, kind = struct.unpack_from("<I4s", data, off)
        if kind == b"JSON":
            return json.loads(data[off + 8:off + 8 + n])
        off += 8 + n + (-n % 4)
    raise ValueError(f"{path}: JSON chunk missing")


def primitive_triangles(g, p):
    # TRIANGLES mode=4. The generated bike uses indexed triangle primitives.
    if p.get("mode", 4) != 4:
        return 0
    if "indices" in p:
        return g["accessors"][p["indices"]]["count"] // 3
    pos = p.get("attributes", {}).get("POSITION")
    return (g["accessors"][pos]["count"] // 3) if pos is not None else 0


def inspect(path: Path):
    g = read_glb(path)
    tris = sum(
        primitive_triangles(g, p)
        for mesh in g.get("meshes", [])
        for p in mesh.get("primitives", [])
    )
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "triangles": tris,
        "nodes": len(g.get("nodes", [])),
        "meshes": len(g.get("meshes", [])),
        "materials": len(g.get("materials", [])),
        "animations": len(g.get("animations", [])),
    }


def main():
    candidates = [
        ROOT / "assets/export/lightcycle.glb",
        *[ROOT / f"assets/export/lightcycle.lod{i}.glb" for i in range(4)],
        ROOT / "assets/export/lightcycle.runtime.glb",
    ]
    rows = [inspect(p) for p in candidates if p.exists()]
    if not rows:
        raise SystemExit("no GLBs found; run npm run build:glb")

    by_name = {Path(r["path"]).name: r for r in rows}
    checks = []
    lod0 = by_name.get("lightcycle.lod0.glb")
    if lod0:
        checks.append({
            "check": "LOD0 hero >= 180,000 tris",
            "pass": lod0["triangles"] >= 180_000,
            "actual": lod0["triangles"],
            "limit": 180_000,
        })
        checks.append({
            "check": "LOD0 hero <= 300,000 tris",
            "pass": lod0["triangles"] <= 300_000,
            "actual": lod0["triangles"],
            "limit": 300_000,
        })
    limits = {1: 150_000, 2: 70_000, 3: 30_000}
    for lod, limit in limits.items():
        name = f"lightcycle.lod{lod}.glb"
        if name in by_name:
            checks.append({
                "check": f"LOD{lod} <= {limit:,} tris",
                "pass": by_name[name]["triangles"] <= limit,
                "actual": by_name[name]["triangles"],
                "limit": limit,
            })

    report = {
        "schema": "lightcycle.static-performance.v1",
        "note": "Static geometry/file-budget evidence only; not hardware FPS evidence.",
        "assets": rows,
        "checks": checks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if any(not c["pass"] for c in checks):
        raise SystemExit("one or more LOD triangle budgets failed")
    print(f"PROFILE OK -> {OUT}")


if __name__ == "__main__":
    main()
