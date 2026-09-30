#!/usr/bin/env python3
"""Generate the neutral PBR texture package used by the canonical Light Cycle.

No player hue is ever written here. Emissive maps are neutral white masks; the
runtime material adapters multiply them by the player's selected energy color.

The package is deterministic and dependency-free so CI and local builds produce
the same bytes without Pillow or a texture-authoring service.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())
OUT = ROOT / "assets/textures/generated"


def png(path: Path, width: int, height: int, channels: int, rows):
    color_type = {1: 0, 3: 2, 4: 6}[channels]
    raw = bytearray()
    for row in rows:
        raw.append(0)  # PNG filter: None
        raw.extend(row)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    payload += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def hex_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def clamp(v):
    return max(0, min(255, int(round(v))))


def noise(x: int, y: int, seed: int) -> float:
    n = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    n ^= (n >> 13)
    n *= 1274126177
    n &= 0xFFFFFFFF
    return ((n >> 8) & 0xFFFF) / 65535.0 * 2.0 - 1.0


def material_style(name: str):
    if name == "MAT_LC_GRAPHITE":
        return "graphite"
    if name == "MAT_LC_BLACK_CLEARCOAT":
        return "clearcoat"
    if name == "MAT_LC_CARBON":
        return "carbon"
    if name == "MAT_LC_MILLED_METAL":
        return "milled"
    if name == "MAT_LC_BRUSHED_METAL":
        return "brushed"
    if name == "MAT_LC_RUBBER":
        return "rubber"
    if name == "MAT_LC_SMOKED_GLASS":
        return "glass"
    return "plain"


def rows_rgb(size, fn):
    for y in range(size):
        row = bytearray()
        for x in range(size):
            row.extend(clamp(v) for v in fn(x, y))
        yield row


def rows_gray(size, fn):
    for y in range(size):
        row = bytearray(clamp(fn(x, y)) for x in range(size))
        yield row


def build_physical(name: str, mat: dict, size: int):
    style = material_style(name)
    base = hex_rgb(mat["baseColor"])
    rough = mat.get("roughness", 0.5) * 255
    metal = mat.get("metallic", 0.0) * 255
    seed = sum(ord(c) for c in name)

    def base_fn(x, y):
        n = noise(x, y, seed)
        delta = 2.5 * n
        if style == "carbon":
            # Small twill weave: alternating diagonal bundles, subtle enough not
            # to look like a printed checkerboard at gameplay distance.
            cell = 7
            a = ((x + y) // cell) & 1
            b = ((x - y) // cell) & 1
            delta += 5 if a == b else -3
        elif style == "milled":
            delta += 2.0 * math.sin((x + y * 0.08) * 0.11)
        elif style == "brushed":
            delta += 2.0 * math.sin(x * 0.55) + 1.2 * math.sin(x * 0.13)
        elif style == "rubber":
            delta += 2.5 * noise(x // 2, y // 2, seed + 31)
        return tuple(c + delta for c in base)

    def rough_fn(x, y):
        n = noise(x, y, seed + 1)
        v = rough + n * 8
        if style == "clearcoat":
            v += 4 * math.sin((x + y) * 0.025)
        elif style == "carbon":
            v += 10 if (((x + y) // 7) & 1) else -6
        elif style == "milled":
            v += 11 * math.sin(x * 0.16)
        elif style == "brushed":
            v += 14 * math.sin(x * 0.42)
        elif style == "rubber":
            v += 17 * noise(x // 3, y // 3, seed + 47)
        return v

    def normal_fn(x, y):
        nx = 0.0
        ny = 0.0
        if style == "carbon":
            parity = (((x + y) // 7) & 1) * 2 - 1
            nx = parity * 0.13
            ny = -parity * 0.13
        elif style in {"milled", "brushed"}:
            nx = 0.08 * math.sin(x * (0.28 if style == "milled" else 0.55))
        elif style == "rubber":
            nx = noise(x, y, seed + 9) * 0.10
            ny = noise(x, y, seed + 10) * 0.10
        elif style == "graphite":
            nx = noise(x, y, seed + 11) * 0.025
            ny = noise(x, y, seed + 12) * 0.025
        nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
        return (127.5 * (nx + 1), 127.5 * (ny + 1), 255 * nz)

    stem = name.lower()
    png(OUT / f"{stem}_basecolor.png", size, size, 3, rows_rgb(size, base_fn))
    png(OUT / f"{stem}_roughness.png", size, size, 1, rows_gray(size, rough_fn))
    png(
        OUT / f"{stem}_metallic.png",
        64, 64, 1,
        (bytes([clamp(metal)]) * 64 for _ in range(64)),
    )
    png(OUT / f"{stem}_normal.png", size, size, 3, rows_rgb(size, normal_fn))
    png(
        OUT / f"{stem}_ao.png",
        128, 128, 1,
        rows_gray(128, lambda x, y: 248 + noise(x, y, seed + 22) * 5),
    )


def build_emissive(name: str):
    # Dedicated emissive geometry means the material itself is the mask. Keeping
    # it neutral is what allows one GLB to become blue/red/gold/purple/green/white.
    stem = name.lower()
    png(
        OUT / f"{stem}_emissive_mask.png",
        128, 128, 1,
        (bytes([255]) * 128 for _ in range(128)),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1024)
    args = ap.parse_args()
    if args.size < 128 or args.size > 4096 or (args.size & (args.size - 1)):
        raise SystemExit("--size must be a power of two from 128 through 4096")

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "lightcycle.textures.v1",
        "neutral": True,
        "playerHueBaked": False,
        "size": args.size,
        "materials": {},
    }

    for name, mat in SPEC["materials"].items():
        if mat.get("emissive"):
            build_emissive(name)
            maps = {"emissiveMask": f"{name.lower()}_emissive_mask.png"}
        else:
            build_physical(name, mat, args.size)
            maps = {
                "baseColor": f"{name.lower()}_basecolor.png",
                "roughness": f"{name.lower()}_roughness.png",
                "metallic": f"{name.lower()}_metallic.png",
                "normal": f"{name.lower()}_normal.png",
                "ao": f"{name.lower()}_ao.png",
            }
        manifest["materials"][name] = maps

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"TEXTURES OK -> {OUT} ({len(manifest['materials'])} materials, neutral runtime color)")


if __name__ == "__main__":
    main()
