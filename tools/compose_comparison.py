#!/usr/bin/env python3
"""Assemble the requested 4-row, 3-column comparison from existing evidence.

Only the supplied reference is cropped. Render pixels are fitted proportionally;
this tool does not recolor, retouch, generate, or substitute any vehicle images.
Originals are never written. A JSON sidecar records source hashes and crop bounds.

    python3 tools/compose_comparison.py --renders assets/render/dark \
        --reference docs/references/02_generated_hybrid_concept.png \
        --out assets/render/reference-comparison.png
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    raise SystemExit("Pillow is required for contact-sheet assembly (Python package PIL).")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCE = ROOT / "docs/references/02_generated_hybrid_concept.png"
DEFAULT_CROP = (0.13, 0.10, 0.85, 0.43)
COLORS = tuple(json.loads((ROOT / "spec/lightcycle.spec.json").read_text())["colors"])


def crop_arg(value: str):
    try:
        bounds = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("crop must be left,top,right,bottom in 0..1") from exc
    if len(bounds) != 4 or not (0 <= bounds[0] < bounds[2] <= 1
                                and 0 <= bounds[1] < bounds[3] <= 1):
        raise argparse.ArgumentTypeError("crop must satisfy 0 <= left < right <= 1 and 0 <= top < bottom <= 1")
    return bounds


def source_image(path: Path):
    """Read/hash/decode one immutable byte snapshot and reject invalid evidence."""
    if not path.is_file():
        raise ValueError(f"Missing input image: {path}")
    try:
        data = path.read_bytes()
        with Image.open(io.BytesIO(data)) as raw:
            raw.load()
            decoded = ImageOps.exif_transpose(raw).convert("RGB")
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError(f"Cannot decode input image {path}: {exc}") from exc
    if decoded.width < 2 or decoded.height < 2:
        raise ValueError(f"Input image has unusable dimensions: {path} ({decoded.size})")
    return decoded, {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "dimensions": list(decoded.size),
    }


def font(size: int, bold: bool = False):
    candidates = [
        Path("/System/Library/Fonts/Supplemental") / ("Arial Bold.ttf" if bold else "Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def plan(args):
    c, a = args.color, args.alternate_color
    # Keep in row-major order: this is the user's requested evidence roster.
    return [
        ("Reference side crop", args.reference, True),
        (f"New side | {c}", args.renders / f"side_{c}.png", False),
        (f"Front three-quarter | {c}", args.renders / f"front34_{c}.png", False),
        (f"Front | {c}", args.renders / f"front_{c}.png", False),
        (f"Top | {c}", args.renders / f"top_{c}.png", False),
        (f"Rear | {c}", args.renders / f"rear_{c}.png", False),
        (f"Front wheel detail | {c}", args.renders / f"wheel_{c}.png", False),
        (f"Reactor detail | {c}", args.renders / f"reactor_{c}.png", False),
        (f"Rear wheel detail | {c}", args.renders / f"rear-wheel_{c}.png", False),
        ("Lights off | side", args.renders / "side_lightsoff.png", False),
        ("Lights off | front three-quarter", args.renders / "front34_lightsoff.png", False),
        (f"Alternate energy | {a}", args.renders / f"front34_{a}.png", False),
    ]


def compose(args):
    roster = plan(args)
    sidecar = args.out.with_suffix(".json")
    output_paths = {args.out.resolve(), sidecar.resolve()}
    if any(path.resolve() in output_paths for _, path, _ in roster):
        raise ValueError("Output paths must not replace any source image.")

    # Decode every required source before making outputs. Never silently replace
    # missing shots with duplicates, reference tiles, or synthetic placeholders.
    evidence = []
    problems = []
    for label, path, is_reference in roster:
        try:
            im, info = source_image(path)
            if is_reference:
                crop = tuple(round(v * (im.width if i % 2 == 0 else im.height))
                             for i, v in enumerate(args.reference_crop))
                if crop[2] <= crop[0] or crop[3] <= crop[1]:
                    raise ValueError("Reference crop contains no image pixels.")
                info["crop_normalized"] = list(args.reference_crop)
                info["crop_pixels"] = list(crop)
                im = im.crop(crop)
            evidence.append((label, im, info, is_reference))
        except ValueError as exc:
            problems.append(str(exc))
    if problems:
        raise ValueError("Cannot assemble comparison:\n  " + "\n  ".join(problems))

    width = args.tile_width
    height = round(width * 9 / 16)
    margin, gap, label_height, header_height = 24, 20, 48, 92
    sheet = Image.new("RGB", (margin * 2 + 3 * width + 2 * gap,
                             margin * 2 + header_height + 4 * (height + label_height) + 3 * gap),
                      "#080d13")
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin), "LIGHT CYCLE / REFERENCE COMPARISON",
              fill="#f0f5fa", font=font(30, True))
    draw.text((margin, margin + 46),
              "1 supplied reference crop + 11 rendered views / Originals preserved",
              fill="#a9b8c6", font=font(18))
    manifest = []
    for index, (label, im, info, is_reference) in enumerate(evidence):
        row, col = divmod(index, 3)
        x = margin + col * (width + gap)
        y = margin + header_height + row * (height + label_height + gap)
        draw.rectangle((x, y, x + width - 1, y + height + label_height - 1), fill="#111a24")
        fitted = ImageOps.contain(im, (width, height), Image.Resampling.LANCZOS)
        px, py = x + (width - fitted.width) // 2, y + (height - fitted.height) // 2
        sheet.paste(fitted, (px, py))
        accent = "#e6bd7b" if is_reference else "#8da8bd"
        draw.line((x, y + height, x + width - 1, y + height), fill=accent, width=2)
        draw.text((x + 13, y + height + 13), f"{index + 1:02d}  {label}",
                  fill="#edf2f7", font=font(18, True))
        manifest.append({"row": row + 1, "column": col + 1, "label": label,
                         "kind": "reference_crop" if is_reference else "render", **info})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out, format="PNG")
    receipt = {
        "schema_version": 1,
        "purpose": "Evidence layout only; no vehicle retouching or generated replacement pixels",
        "output": str(args.out.resolve()),
        "output_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
        "dimensions": list(sheet.size),
        "rows": 4,
        "columns": 3,
        "color": args.color,
        "alternate_color": args.alternate_color,
        "sources": manifest,
    }
    sidecar.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"COMPARISON OK -> {args.out}\nSOURCE RECEIPT -> {sidecar}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--renders", type=Path, default=ROOT / "assets/render/dark",
                    help="Directory containing required render PNGs")
    ap.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    ap.add_argument("--out", type=Path, default=ROOT / "assets/render/reference-comparison.png")
    ap.add_argument("--color", default="red", choices=COLORS)
    ap.add_argument("--alternate-color", default="blue", choices=COLORS)
    ap.add_argument("--reference-crop", type=crop_arg, default=DEFAULT_CROP,
                    help="Normalized left,top,right,bottom (default: 0.13,0.10,0.85,0.43)")
    ap.add_argument("--tile-width", type=int, default=640)
    args = ap.parse_args()
    if args.color == args.alternate_color:
        ap.error("--alternate-color must differ from --color")
    if not 480 <= args.tile_width <= 1920:
        ap.error("--tile-width must be between 480 and 1920")
    if args.out.suffix.lower() != ".png":
        ap.error("--out must end in .png")
    try:
        compose(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
