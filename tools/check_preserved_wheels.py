#!/usr/bin/env python3
"""Fingerprint preserved wheel engineering in uncompressed canonical GLBs.

Ordinary check (no baseline GLB needed):
  python3 tools/check_preserved_wheels.py assets/export/lightcycle.glb

Explicit first-time baseline capture from a known original artifact:
  python3 tools/check_preserved_wheels.py /path/original.glb \
    --write-baseline docs/handoff/WHEEL_BASELINE.json --source-commit COMMIT

The hard gate covers indexed triangle surfaces, material slots and named pivot
ancestry at a measured 1e-6-metre tolerance. Exporter vertex splits/order do not
fail that gate. Normal and UV drift is always reported separately as shading
evidence requiring review; a geometry pass does not certify unchanged shading.
Packed/quantized assets must use their separate contract validator.
"""
from __future__ import annotations

import argparse
import base64
from collections import defaultdict
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIMS = json.loads((ROOT / "spec/lightcycle.spec.json").read_text())["dimensions_m"]
PARTS = ("OuterRing", "InnerRing", "Bearing", "EnergyRing", "BrakeDisc",
         "Caliper_L", "Caliper_R", "Suspension")
PROTECTED = tuple(sorted([f"LC_Wheel_{end}_{part}" for end in ("Front", "Rear")
                          for part in PARTS] + ["LC_RearDrive"]))
COMPONENTS = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
              5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


class CanonicalGLB:
    def __init__(self, path: Path):
        data = path.read_bytes()
        self.sha256 = hashlib.sha256(data).hexdigest()
        if len(data) < 20 or struct.unpack_from("<4sII", data) != (b"glTF", 2, len(data)):
            raise ValueError("Invalid or truncated GLB 2 header")
        chunks = {}
        offset = 12
        while offset < len(data):
            if offset + 8 > len(data):
                raise ValueError("Truncated GLB chunk header")
            length, kind = struct.unpack_from("<I4s", data, offset)
            end = offset + 8 + length
            if end > len(data) or length % 4:
                raise ValueError("Invalid GLB chunk length")
            if kind in chunks:
                raise ValueError(f"Repeated GLB chunk: {kind!r}")
            chunks[kind] = data[offset + 8:end]
            offset = end
        if b"JSON" not in chunks or b"BIN\0" not in chunks:
            raise ValueError("Canonical GLB requires JSON and embedded BIN chunks")
        self.g = json.loads(chunks[b"JSON"])
        self.binary = chunks[b"BIN\0"]
        buffers = self.g.get("buffers", [])
        if len(buffers) != 1 or "uri" in buffers[0] or buffers[0]["byteLength"] > len(self.binary):
            raise ValueError("Only one embedded canonical buffer is supported")
        if any(ext in self.g.get("extensionsRequired", []) for ext in
               ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_mesh_quantization")):
            raise ValueError("Use the original uncompressed canonical GLB, not a packed runtime asset")
        self.cache = {}
        self.decoded_cache = {}

    def values(self, view_id, offset, count, component, width, allow_stride=True):
        view = self.g["bufferViews"][view_id]
        if view.get("buffer", 0) != 0 or view.get("extensions"):
            raise ValueError("Compressed or external accessor buffer is unsupported")
        code, byte_width = COMPONENTS[component]
        element_size = byte_width * width
        stride = view.get("byteStride", element_size) if allow_stride else element_size
        start = view.get("byteOffset", 0) + offset
        extent = offset + ((count - 1) * stride + element_size if count else 0)
        if stride < element_size or offset < 0 or extent > view["byteLength"]:
            raise ValueError("Accessor exceeds its bufferView")
        if start + max(0, extent - offset) > len(self.binary):
            raise ValueError("Accessor exceeds embedded buffer")
        return [struct.unpack_from("<" + code * width, self.binary, start + i * stride)
                for i in range(count)]

    def decoded(self, index):
        if index in self.decoded_cache:
            return self.decoded_cache[index]
        a = self.g["accessors"][index]
        component, count = a["componentType"], a["count"]
        if a["type"] not in WIDTHS or component not in COMPONENTS or count < 0:
            raise ValueError("Unsupported canonical accessor type/count")
        width = WIDTHS[a["type"]]
        values = self.values(a["bufferView"], a.get("byteOffset", 0), count, component, width) \
            if "bufferView" in a else [(0,) * width for _ in range(count)]
        if "sparse" in a:
            sparse = a["sparse"]
            ix, val = sparse["indices"], sparse["values"]
            if ix["componentType"] not in (5121, 5123, 5125):
                raise ValueError("Invalid sparse index component type")
            indices = self.values(ix["bufferView"], ix.get("byteOffset", 0), sparse["count"],
                                  ix["componentType"], 1, False)
            replacements = self.values(val["bufferView"], val.get("byteOffset", 0), sparse["count"],
                                       component, width, False)
            last = -1
            for (i,), value in zip(indices, replacements):
                if not last < i < count:
                    raise ValueError("Sparse accessor indices must be ordered and in range")
                values[i] = value
                last = i
        decoded = []
        for row in values:
            converted = []
            for value in row:
                if a.get("normalized"):
                    if component in (5120, 5122):
                        value = max(value / (127 if component == 5120 else 32767), -1.0)
                    elif component in (5121, 5123, 5125):
                        value /= {5121: 255, 5123: 65535, 5125: 4294967295}[component]
                    else:
                        raise ValueError("Floating point accessor cannot be normalized")
                if not math.isfinite(value):
                    raise ValueError("Non-finite geometry accessor value")
                converted.append(0.0 if value == 0 else value)
            decoded.append(tuple(converted))
        self.decoded_cache[index] = decoded
        return decoded

    def accessor(self, index):
        if index in self.cache:
            return self.cache[index]
        a = self.g["accessors"][index]
        digest = hashlib.sha256()
        for row in self.decoded(index):
            for value in row:
                digest.update(struct.pack("<d", value))
        result = {"type": a["type"], "component_type": a["componentType"], "count": a["count"],
                  "normalized": bool(a.get("normalized", False)), "sha256": digest.hexdigest()}
        self.cache[index] = result
        return result

    def triangle_evidence(self, primitive):
        if primitive.get("mode", 4) != 4:
            raise ValueError("Protected canonical wheel geometry must use TRIANGLES")
        attrs = {name: self.decoded(i) for name, i in primitive["attributes"].items()}
        if any(self.g["accessors"][primitive["attributes"][name]]["componentType"] != 5126
               for name in ("POSITION", "NORMAL")):
            raise ValueError("Canonical POSITION/NORMAL must use uncompressed FLOAT accessors")
        positions, normals = attrs["POSITION"], attrs["NORMAL"]
        if len(positions) != len(normals):
            raise ValueError("Position/normal accessor lengths differ")
        if "indices" in primitive:
            accessor = self.g["accessors"][primitive["indices"]]
            if accessor["type"] != "SCALAR" or accessor["componentType"] not in (5121, 5123, 5125):
                raise ValueError("Triangle indices must use unsigned scalar accessors")
            indices = [int(row[0]) for row in self.decoded(primitive["indices"])]
        else:
            indices = list(range(len(positions)))
        if len(indices) % 3 or any(not isinstance(i, int) or not 0 <= i < len(positions) for i in indices):
            raise ValueError("Invalid canonical triangle index stream")
        rows = []
        uv_rows = {name: [] for name in attrs if name.startswith("TEXCOORD_")}
        for offset in range(0, len(indices), 3):
            triangle = indices[offset:offset + 3]
            corners = [positions[i] + normals[i] for i in triangle]
            keys = [position_key(corner) for corner in corners]
            first = min(range(3), key=lambda i: tuple(keys[i:] + keys[:i]))
            order = triangle[first:] + triangle[:first]
            key = tuple(keys[first:] + keys[:first])
            values = tuple(value for i in order for value in positions[i] + normals[i])
            rows.append((key, values))
            for name in uv_rows:
                uv_rows[name].append((key, tuple(value for i in order for value in attrs[name][i])))
        rows.sort()
        payload = b"".join(struct.pack("<18f", *values) for _, values in rows)
        return {
            "triangle_count": len(rows),
            "corner_encoding": "zlib+base64 / little-endian 18 float32 per triangle / xyz,nxyz per corner",
            "corners_sha256": hashlib.sha256(payload).hexdigest(),
            "corners": base64.b64encode(zlib.compress(payload, 9)).decode("ascii"),
            "uv_triangle_sha256": {
                name: hashlib.sha256(b"".join(struct.pack("<" + "d" * len(values), *values)
                                            for _, values in sorted(uvs))).hexdigest()
                for name, uvs in uv_rows.items()
            },
        }

    def fingerprint(self):
        nodes = self.g["nodes"]
        by_name = {}
        parents = {}
        for i, node in enumerate(nodes):
            name = node.get("name")
            if name:
                if name in by_name:
                    raise ValueError(f"Duplicate node name: {name}")
                by_name[name] = i
            for child in node.get("children", []):
                if child in parents:
                    raise ValueError("Node has multiple parents")
                parents[child] = i
        missing = set(PROTECTED) - by_name.keys()
        if missing:
            raise ValueError(f"Missing protected meshes: {sorted(missing)}")
        selected = set()
        for name in PROTECTED:
            i, chain = by_name[name], set()
            while True:
                if i in chain:
                    raise ValueError("Cycle in protected node ancestry")
                chain.add(i)
                selected.add(i)
                if i not in parents:
                    break
                i = parents[i]
        result = {}
        for i in selected:
            node = nodes[i]
            name = node.get("name")
            if not name:
                raise ValueError("Protected canonical ancestry must have named nodes")
            transform = {"matrix": node["matrix"]} if "matrix" in node else {
                "translation": node.get("translation", [0, 0, 0]),
                "rotation": node.get("rotation", [0, 0, 0, 1]),
                "scale": node.get("scale", [1, 1, 1]),
            }
            item = {"parent": nodes[parents[i]].get("name") if i in parents else None,
                    "transform": transform}
            if name in PROTECTED:
                if "mesh" not in node or "skin" in node:
                    raise ValueError(f"Expected independent unskinned mesh: {name}")
                mesh = self.g["meshes"][node["mesh"]]
                primitives = []
                for p in mesh["primitives"]:
                    if "POSITION" not in p["attributes"] or "NORMAL" not in p["attributes"]:
                        raise ValueError(f"Missing POSITION/NORMAL for {name}")
                    if p.get("extensions"):
                        raise ValueError(f"Unsupported primitive extension for {name}")
                    material = self.g["materials"][p["material"]].get("name") if "material" in p else None
                    primitives.append({
                        "mode": p.get("mode", 4), "material": material,
                        "attributes": {key: self.accessor(value) for key, value in sorted(p["attributes"].items())},
                        "indices": self.accessor(p["indices"]) if "indices" in p else None,
                        "targets": [{key: self.accessor(value) for key, value in sorted(target.items())}
                                    for target in p.get("targets", [])],
                        "triangle_evidence": self.triangle_evidence(p),
                    })
                item["mesh"] = {"primitives": primitives, "weights": mesh.get("weights", [])}
            result[name] = item
        return dict(sorted(result.items()))


def position_key(corner):
    # This 10-micrometre grid is only a correspondence lookup. Matching triangles
    # still undergo the stricter measured 1-micrometre position-delta gate below.
    return tuple(round(value * 100000) for value in corner[:3])


def contract_view(nodes):
    result = {}
    for name, node in nodes.items():
        item = {key: value for key, value in node.items() if key != "mesh"}
        if "mesh" in node:
            item["mesh"] = {
                "weights": node["mesh"]["weights"],
                "primitives": [{"mode": p["mode"], "material": p["material"],
                                "attribute_names": sorted(p["attributes"]), "targets": p["targets"]}
                               for p in node["mesh"]["primitives"]],
            }
        result[name] = item
    return result


def architecture_view(nodes):
    """Preserve wheel assembly ownership/topology while allowing approved dimensions to move."""
    result = {}
    for name, node in nodes.items():
        item = {"parent": node["parent"]}
        if "mesh" in node:
            item["mesh"] = {
                "weights": node["mesh"]["weights"],
                "primitives": [{
                    "mode": p["mode"], "material": p["material"],
                    "attribute_names": sorted(p["attributes"]), "targets": p["targets"],
                } for p in node["mesh"]["primitives"]],
            }
        result[name] = item
    return result


def raw_view(nodes):
    return {name: {**node, "mesh": {**node["mesh"], "primitives": [
        {k: v for k, v in p.items() if k != "triangle_evidence"}
        for p in node["mesh"]["primitives"]]}} if "mesh" in node else node
            for name, node in nodes.items()}


def triangle_groups(evidence):
    payload = zlib.decompress(base64.b64decode(evidence["corners"], validate=True))
    if len(payload) != evidence["triangle_count"] * 72 or hashlib.sha256(payload).hexdigest() != evidence["corners_sha256"]:
        raise ValueError("Baseline triangle payload has invalid length/hash")
    groups = defaultdict(list)
    for values in struct.iter_unpack("<18f", payload):
        corners = tuple(values[i:i + 6] for i in (0, 6, 12))
        groups[tuple(position_key(corner) for corner in corners)].append(corners)
    return groups


def geometric_comparison(expected, actual, position_tolerance, normal_tolerance):
    left, right = triangle_groups(expected), triangle_groups(actual)
    missing = sum(max(len(left[key]) - len(right[key]), 0) for key in left.keys() | right.keys())
    added = sum(max(len(right[key]) - len(left[key]), 0) for key in left.keys() | right.keys())
    max_position = max_component = max_normal = max_angle = 0.0
    matched = 0
    for key in left.keys() & right.keys():
        # Coincident triangles are paired deterministically by corner normals.
        normal_key = lambda triangle: tuple(v for corner in triangle for v in corner[3:])
        for a, b in zip(sorted(left[key], key=normal_key), sorted(right[key], key=normal_key)):
            matched += 1
            for av, bv in zip(a, b):
                delta = [abs(x - y) for x, y in zip(av[:3], bv[:3])]
                max_component = max(max_component, *delta)
                max_position = max(max_position, math.sqrt(sum(v * v for v in delta)))
                max_normal = max(max_normal, *(abs(x - y) for x, y in zip(av[3:], bv[3:])))
                lengths = math.sqrt(sum(v * v for v in av[3:]) * sum(v * v for v in bv[3:]))
                if lengths == 0:
                    raise ValueError("Zero-length normal in protected geometry")
                cosine = sum(x * y for x, y in zip(av[3:], bv[3:])) / lengths
                max_angle = max(max_angle, math.degrees(math.acos(max(-1, min(1, cosine)))))
    return {
        "geometry_passed": missing == added == 0 and max_position <= position_tolerance,
        "normals_within_diagnostic_tolerance": missing == added == 0 and max_normal <= normal_tolerance,
        "uv_unchanged": expected["uv_triangle_sha256"] == actual["uv_triangle_sha256"],
        "matched_triangles": matched, "unmatched_baseline_triangles": missing,
        "unmatched_candidate_triangles": added, "max_position_delta_m": max_position,
        "max_position_component_delta_m": max_component,
        "max_normal_component_delta": max_normal, "max_normal_angle_degrees": max_angle,
    }


def differences(expected, actual, path="nodes"):
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            child = f"{path}.{key}"
            if key not in expected:
                yield f"{child}: added"
            elif key not in actual:
                yield f"{child}: missing"
            else:
                yield from differences(expected[key], actual[key], child)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            yield f"{path}: length changed from {len(expected)} to {len(actual)}"
        for i, (a, b) in enumerate(zip(expected, actual)):
            yield from differences(a, b, f"{path}[{i}]")
    elif expected != actual:
        yield f"{path}: changed from {expected!r} to {actual!r}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb", type=Path)
    ap.add_argument("--baseline", type=Path, default=ROOT / "docs/handoff/WHEEL_BASELINE.json")
    ap.add_argument("--write-baseline", type=Path)
    ap.add_argument("--source-commit")
    ap.add_argument("--source-note", default="")
    ap.add_argument("--report", type=Path, help="Optional JSON check result; never rewrites a GLB")
    ap.add_argument("--position-tolerance", type=float, default=1e-6, help="Maximum measured corner displacement in metres (default 1e-6)")
    ap.add_argument("--normal-tolerance", type=float, default=1e-5, help="Diagnostic threshold for normal shading drift; not a geometry gate (default 1e-5)")
    args = ap.parse_args()
    try:
        if not all(math.isfinite(v) and v >= 0 for v in (args.position_tolerance, args.normal_tolerance)):
            raise ValueError("Tolerances must be finite, nonnegative numbers")
        glb = CanonicalGLB(args.glb)
        current = glb.fingerprint()
        if args.write_baseline:
            if not args.source_commit or len(args.source_commit) != 40:
                raise ValueError("Baseline capture requires an explicit full --source-commit")
            if args.write_baseline.exists():
                raise ValueError("Refusing to replace an existing wheel baseline")
            baseline = {"schema_version": 2, "artifact": "uncompressed canonical GLB",
                        "source_commit": args.source_commit, "source_glb": str(args.glb.resolve()),
                        "source_glb_sha256": glb.sha256, "source_note": args.source_note,
                        "protected_mesh_nodes": list(PROTECTED),
                        "excluded": {"LC_SteeringYoke": "Existing world-origin pivot is being repaired separately"},
                        "nodes": current}
            args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
            args.write_baseline.write_text(json.dumps(baseline, indent=2) + "\n")
            print(f"BASELINE RECORDED: {len(PROTECTED)} meshes, {len(current)} nodes -> {args.write_baseline}")
            return 0
        baseline = json.loads(args.baseline.read_text())
        if baseline.get("schema_version") != 2 or baseline.get("protected_mesh_nodes") != list(PROTECTED):
            raise ValueError("Unrecognized baseline schema or protected mesh roster")
        reference_revision = DIMS.get("wheelReferenceRevision")
        if reference_revision:
            # The user rejected the old visible wheel proportions against exact references.
            # Keep topology/material/parent architecture stable while allowing coordinates,
            # section width, hub void and axle spacing to change deliberately.
            errors = list(differences(architecture_view(baseline["nodes"]), architecture_view(current)))
            for name, sign in (("LC_Wheel_Front", -1), ("LC_Wheel_Rear", 1)):
                tr = current[name]["transform"].get("translation")
                expected = [sign * DIMS["wheelbase"] / 2, DIMS["wheelOuterDiameter"] / 2, 0]
                if tr is None or any(abs(float(a)-float(b)) > 1e-5 for a,b in zip(tr, expected)):
                    errors.append(f"{name}: axle pivot {tr!r} does not match reference dimensions {expected!r}")
        else:
            errors = list(differences(contract_view(baseline["nodes"]), contract_view(current)))
        raw_differences = list(differences(raw_view(baseline["nodes"]), raw_view(current)))
        measurements = {}
        for name in PROTECTED:
            a = baseline["nodes"][name]["mesh"]["primitives"]
            b = current[name]["mesh"]["primitives"]
            for i, (left, right) in enumerate(zip(a, b)):
                measurement = geometric_comparison(left["triangle_evidence"], right["triangle_evidence"],
                                                   args.position_tolerance, args.normal_tolerance)
                measurements[f"{name}.primitive[{i}]"] = measurement
                if not measurement["geometry_passed"] and not reference_revision:
                    errors.append(f"{name}.primitive[{i}]: position/topology preservation failed")
        shading_review = any(not m["normals_within_diagnostic_tolerance"] or not m["uv_unchanged"]
                             for m in measurements.values())
        report = {"passed": not errors, "candidate_glb": str(args.glb.resolve()),
                  "reference_shape_revision": reference_revision,
                  "pass_scope": ("Topology/triangle counts, material ownership, parent architecture and axle pivots; "
                                 "coordinate deltas are diagnostic during the explicit reference-shape revision"
                                 if reference_revision else
                                 "Triangle surfaces/topology, material slot ownership, parent and pivot contracts only"),
                  "shading_review_required": shading_review,
                  "candidate_glb_sha256": glb.sha256, "baseline": str(args.baseline.resolve()),
                  "baseline_source_commit": baseline["source_commit"],
                  "baseline_source_glb_sha256": baseline["source_glb_sha256"],
                  "protected_mesh_count": len(PROTECTED), "contract_node_count": len(current),
                  "position_tolerance_m": args.position_tolerance,
                  "normal_component_tolerance": args.normal_tolerance,
                  "correspondence_grid_m": 1e-5,
                  "raw_accessor_layout_unchanged": not raw_differences,
                  "uv_unchanged": all(m["uv_unchanged"] for m in measurements.values()),
                  "differences": errors, "measurements": measurements,
                  "raw_accessor_differences": raw_differences}
        if args.report:
            if args.report.resolve() in {args.glb.resolve(), args.baseline.resolve()}:
                raise ValueError("Report must not overwrite the GLB or baseline")
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n")
        for error in errors:
            print(f"FAIL {error}")
        for name, measurement in measurements.items():
            if not measurement["normals_within_diagnostic_tolerance"]:
                print(f"SHADING REVIEW {name}: max normal component delta "
                      f"{measurement['max_normal_component_delta']:.9g}, "
                      f"angle {measurement['max_normal_angle_degrees']:.6g} degrees")
        uv_count = sum(not m["uv_unchanged"] for m in measurements.values())
        print(f"Accessor layout differences: {len(raw_differences)}; UV-changed primitives: {uv_count}")
        print(f"Measured maxima: position {max(m['max_position_delta_m'] for m in measurements.values()):.9g} m; "
              f"normal component {max(m['max_normal_component_delta'] for m in measurements.values()):.9g}")
        if shading_review:
            print("SHADING REVIEW PENDING: geometry preservation does not certify unchanged normals or UVs")
        if reference_revision:
            print(f"REFERENCE WHEEL REVISION: {reference_revision}; coordinate deltas are expected and reported")
        print(f"WHEEL GEOMETRY/CONTRACT {'PASS' if not errors else 'FAIL'}: {len(PROTECTED)} meshes, "
              f"{len(current)} nodes, {len(errors)} differences")
        return 1 if errors else 0
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error, zlib.error) as exc:
        print(f"WHEEL PRESERVATION ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
