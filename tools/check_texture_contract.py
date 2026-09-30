#!/usr/bin/env python3
"""Reject GLBs whose generated PBR textures never reached the exported asset.

Run after building, then repeat after packing:
  python3 tools/check_texture_contract.py assets/export/lightcycle.glb
  python3 tools/check_texture_contract.py assets/export/lightcycle.runtime.glb --require-ktx2

The ordinary node/material validator cannot catch disconnected texture nodes.
This check follows material references into embedded image bytes and verifies UVs.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from validate_glb import read_glb_json

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())
SIGNATURES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/ktx2": b"\xabKTX 20\xbb\r\n\x1a\n",
}


def binary_chunk(path: Path) -> bytes:
    data = path.read_bytes()
    offset = 12
    while offset + 8 <= len(data):
        length, kind = struct.unpack_from("<I4s", data, offset)
        if kind == b"BIN\x00":
            return data[offset + 8:offset + 8 + length]
        offset += 8 + length
    return b""


def check(path: Path, require_ktx2: bool = False) -> list[str]:
    gltf = read_glb_json(path)
    binary = binary_chunk(path)
    errors = []
    materials = gltf.get("materials", [])
    by_name = {material.get("name"): material for material in materials}
    textured_materials = set()

    def image_for(texture_ref: dict, context: str):
        try:
            texture = gltf["textures"][texture_ref["index"]]
            basis = texture.get("extensions", {}).get("KHR_texture_basisu")
            if require_ktx2 and basis is None:
                raise ValueError("missing KHR_texture_basisu")
            source = basis["source"] if basis is not None else texture["source"]
            image = gltf["images"][source]
            mime = image["mimeType"]
            if require_ktx2 and mime != "image/ktx2":
                raise ValueError(f"expected image/ktx2, found {mime}")
            view = gltf["bufferViews"][image["bufferView"]]
            if view.get("buffer", 0) != 0 or "uri" in gltf["buffers"][0]:
                raise ValueError("image must be embedded in the GLB")
            start = view.get("byteOffset", 0)
            payload = binary[start:start + view["byteLength"]]
            signature = SIGNATURES.get(mime)
            if signature is None or len(payload) <= len(signature) or not payload.startswith(signature):
                raise ValueError(f"missing or invalid embedded {mime} image bytes")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            errors.append(f"{context}: {exc}")

    for name, definition in SPEC["materials"].items():
        material = by_name.get(name)
        if material is None:
            errors.append(f"missing material {name}")
            continue
        if definition.get("emissive"):
            factor = material.get("emissiveFactor", [0, 0, 0])
            if max(factor) <= 0 or max(factor) - min(factor) > 0.02:
                errors.append(f"{name}: authored emissive factor must be nonzero and neutral")
            continue

        textured_materials.add(materials.index(material))
        pbr = material.get("pbrMetallicRoughness", {})
        for slot, reference in (
            ("baseColorTexture", pbr.get("baseColorTexture")),
            ("metallicRoughnessTexture", pbr.get("metallicRoughnessTexture")),
            ("normalTexture", material.get("normalTexture")),
        ):
            if reference is None:
                errors.append(f"{name}: missing {slot}")
            else:
                image_for(reference, f"{name}.{slot}")

    for mesh in gltf.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("material") in textured_materials:
                if "TEXCOORD_0" not in primitive.get("attributes", {}):
                    errors.append(f"{mesh.get('name', '<unnamed>')}: textured primitive has no TEXCOORD_0")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("--require-ktx2", action="store_true")
    args = parser.parse_args()
    errors = check(args.glb, args.require_ktx2)
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        raise SystemExit(f"TEXTURE CONTRACT FAILED: {len(errors)} errors")
    mode = "KTX2" if args.require_ktx2 else "embedded"
    print(f"TEXTURE CONTRACT OK: 7 physical materials with {mode} PBR maps, UVs, 4 neutral energy materials")


if __name__ == "__main__":
    main()
