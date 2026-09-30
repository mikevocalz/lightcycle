#!/usr/bin/env python3
"""Produce the compressed runtime GLB from the validated canonical one.

    tools/pack_runtime.py

Deliberately a SEPARATE step, not a flag on the Blender export, for two reasons
found by testing gltfpack against the real asset:

1. gltfpack's default run DESTROYS the node contract - LC_Reactor_Core,
   LC_FX_TrailOrigin, LC_FX_Boost, LC_FX_CrashCenter and LC_FX_DerezCenter all
   disappear, and validate_glb.py fails. `-kn` (keep named nodes) fixes it
   completely: all 102 names survive with correct parenting. Blender's
   export_gltfpack_kn defaults to False, so wiring gltfpack into the main export
   would silently ship a broken asset.

2. Blender's export_use_gltfpack writes into a `gltfpacked/` SUBDIRECTORY rather
   than the requested path, and swallows CalledProcessError - so a failed pack
   reports success and leaves the plain file in place. Calling gltfpack directly
   means a failure is a failure.

The canonical GLB stays uncompressed and remains the thing CI validates.

Note: gltfpack strips all node `extras` and there is no flag to keep them. That
costs nothing here - the lc_* tags are DCC-side bookkeeping, and the runtime
reads spec/ for roles, never the GLB's extras.
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/export/lightcycle.glb"
OUT = ROOT / "assets/export/lightcycle.runtime.glb"


def main() -> int:
    exe = shutil.which("gltfpack")
    if not exe:
        sys.exit("gltfpack not on PATH. Install the NATIVE build from\n"
                 "  https://github.com/zeux/meshoptimizer/releases\n"
                 "The npm package is a Node/WASM build with no BasisU support and "
                 "cannot produce KTX2 at all.")
    if not SRC.exists():
        sys.exit(f"{SRC} missing - run npm run build:glb first")

    # -kn keeps named nodes (the contract). -tc encodes textures to KTX2/BasisU.
    cmd = [exe, "-i", str(SRC), "-o", str(OUT), "-kn", "-tc"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, sep="\n")
        sys.exit(f"gltfpack failed ({r.returncode})")

    before, after = SRC.stat().st_size, OUT.stat().st_size
    print(f"{before:,} -> {after:,} bytes  ({100 * (1 - after / before):.0f}% smaller)")

    # The compressed artifact has to honour the same contract as the canonical one.
    v = subprocess.run([sys.executable, str(ROOT / "tools/validate_glb.py"), str(OUT)],
                       capture_output=True, text=True)
    print(v.stdout.strip().splitlines()[-1] if v.stdout else "")
    if v.returncode != 0:
        print(v.stdout)
        sys.exit("packed GLB breaks the node contract - do not ship it")
    print(f"packed -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
