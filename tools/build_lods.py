#!/usr/bin/env python3
"""Build and contract-validate LOD0..LOD3 from the canonical source blend."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLEND = ROOT / "assets/source/lightcycle_blockout.blend"
EXPORTER = ROOT / "tools/lod_export.py"
VALIDATOR = ROOT / "tools/validate_glb.py"


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        raise SystemExit(r.returncode)


def pack_lod(gltfpack: str, lod: int):
    src = ROOT / f"assets/export/lightcycle.lod{lod}.glb"
    out = ROOT / f"assets/export/lightcycle.lod{lod}.runtime.glb"
    run([gltfpack, "-i", str(src), "-o", str(out), "-kn", "-tc"])
    run([sys.executable, str(VALIDATOR), str(out)])
    print(f"LOD{lod} runtime -> {out}")


def main():
    blender = shutil.which("blender")
    if not blender:
        raise SystemExit("blender not on PATH")
    if not BLEND.exists():
        raise SystemExit(f"{BLEND} missing; run npm run build:glb first")
    gltfpack = shutil.which("gltfpack")
    if not gltfpack:
        raise SystemExit("gltfpack not on PATH; runtime LODs require native KTX2 packing")

    for lod in range(4):
        out = ROOT / f"assets/export/lightcycle.lod{lod}.glb"
        if out.exists():
            out.unlink()
        run([blender, "-b", str(BLEND), "-P", str(EXPORTER), "--", "--lod", str(lod)])
        if not out.exists() or out.stat().st_size < 1024:
            raise SystemExit(f"LOD{lod} exporter did not produce a fresh GLB: {out}")
        run([sys.executable, str(VALIDATOR), str(out)])
        pack_lod(gltfpack, lod)

    print("LOD CHAIN OK: LOD0..LOD3 exported, KTX2-packed, and contract validated")


if __name__ == "__main__":
    main()
