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


def main():
    blender = shutil.which("blender")
    if not blender:
        raise SystemExit("blender not on PATH")
    if not BLEND.exists():
        raise SystemExit(f"{BLEND} missing; run npm run build:glb first")

    for lod in range(4):
        out = ROOT / f"assets/export/lightcycle.lod{lod}.glb"
        run([blender, "-b", str(BLEND), "-P", str(EXPORTER), "--", "--lod", str(lod)])
        run([sys.executable, str(VALIDATOR), str(out)])

    print("LOD CHAIN OK: LOD0..LOD3 exported and node/clip contract validated")


if __name__ == "__main__":
    main()
