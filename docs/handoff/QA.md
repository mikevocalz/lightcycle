# Current visual evidence

The final candidate is retained at `../review/reference-comparison.png`, with
individual captures/receipts under `../review/renders` and six clay views under
`../review/clay`. Latest primary reference is the user's white board
`../references/00_generated_hybrid_concept.png.png`; reference02 was used in earlier
passes. The user confirmed preserving current wheels while matching visible body
proportions. No human visual approval is recorded. Browser QA results/screenshots
are also retained in `../review`. Actual matrix execution:20 CI captures +63 full.

# Reference comparison and visual QA

The requested final comparison is four rows by three columns. Its first tile is
a crop of the supplied reference board; the other eleven tiles must be fresh
Blender renders of the candidate geometry. A composed sheet alone does not prove
art approval, runtime parity, or headset performance.

## Earlier reference identity (reference02; historical)

- Source: `docs/references/02_generated_hybrid_concept.png`.
- Inspected dimensions: 1448 × 1086.
- SHA-256: `2bcfc07c94fb7f48652c21b65093c15713756458df7b6f3b93cd5e1cd9e92747`.
- This is the red-energy board with a large riderless side view, front/top/rear
  views beneath, and three detail panels along the bottom.
- The default side crop is normalized `(left=0.13, top=0.10, right=0.85,
  bottom=0.43)`, or pixels `(188, 109, 1231, 467)` at the inspected resolution.
  It includes both complete tires, body, and floor contact without the board's
  lower views. The original board stays unchanged.
- `docs/references/01_generated_hybrid_concept.png` is also useful for silhouette
  evaluation. It does not silently replace the board in the requested sheet.

## Required contact-sheet roster

Render filenames are relative to the `--renders` directory. Defaults use red as
the primary energy hue and blue as the alternate. Both hues use the same asset.

| Row | Column 1 | Column 2 | Column 3 |
| --- | --- | --- | --- |
| 1 | Supplied board side crop | `side_red.png` | `front34_red.png` |
| 2 | `front_red.png` | `top_red.png` | `rear_red.png` |
| 3 | `wheel_red.png` | `reactor_red.png` | `rear-wheel_red.png` |
| 4 | `side_lightsoff.png` | `front34_lightsoff.png` | `front34_blue.png` |

`wheel` is the existing front-wheel detail name; the renderer also supports a
`front-wheel` alias. The contact sheet deliberately uses `wheel` for compatibility.
`side`, `front`, `rear`, and `top` are orthographic cameras. Three-quarter and
detail captures retain perspective. Keep camera framing stable when comparing
geometry revisions. Lights-off means energy emission is zero; studio lights
remain available so the materials and construction can be assessed.

## Capture and compose

First ensure the candidate `.blend` has been rebuilt and validated. Use a fresh
output directory for each revision to avoid mixing old and new shots. From the
repository root, the following captures the primary views and their lights-off
counterparts; the alternate command adds the final blue three-quarter view:

```bash
blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --matrix --matrix-colors red --matrix-views side,front34,front,top,rear,wheel,reactor,rear-wheel --engine BLENDER_EEVEE --samples 32 --res 1280 --context dark --output-dir assets/render/reference-review
blender -b assets/source/lightcycle_blockout.blend -P tools/render_matrix.py -- --color blue --view front34 --engine BLENDER_EEVEE --samples 32 --res 1280 --context dark --output-dir assets/render/reference-review
python3 tools/compose_comparison.py --renders assets/render/reference-review --reference docs/references/00_generated_hybrid_concept.png.png --out assets/render/reference-comparison.png
```

These are reproducible commands, not a claim they have all completed. Consult the
active handoff status and capture files for actual execution evidence.

The composer requires Pillow (`PIL`), already present in the inspected Python
environment. It validates and decodes all twelve inputs before writing outputs.
Missing or corrupt images fail explicitly, with no placeholder or substituted
view. It writes a PNG and same-stem JSON receipt recording the source paths,
SHA-256 hashes, input sizes, reference crop, tile positions, and output hash. It
never writes into a source image path. `--color`, `--alternate-color`,
`--reference-crop`, and `--tile-width` are optional overrides. Render images are
fitted proportionally with no crop or color retouching; only the reference tile
uses the declared crop.

The render tool writes a same-stem JSON capture record for each PNG. Preserve
those records alongside the comparison receipt. The composer reports file
identity; it does not independently certify that a PNG was produced by Blender.

## Inspect before claiming completion

1. Inspect a neutral clay suite before polishing light or materials. Check full
   side silhouette, empty wheel centers, width/taper, body flow, cockpit placement,
   tail, and front/rear construction against the source references.
2. Inspect each final capture and the full sheet. Check body panel depth, tire
   cross section, wheel bearing detail, reactor proportions, believable support
   construction, and whether the chassis holds up with emission disabled.
3. Verify the canonical GLB and packed GLB retain the contract, runtime color
   selection, neutral emissive masks, pivots, and animation names. Do not equate a
   Blender beauty render with runtime correctness.
4. Run appropriate renderer adapter tests and type checking; regenerate LOD,
   static budget, and rider evidence after geometry changes when the revision is
   ready for those gates. A static budget is not a measured hardware frame time.
5. Record the inspected candidate source hash, specific artifacts, remaining
   deviations, and actual outcomes in the main handoff. Keep human art direction
   and real XR hardware review explicitly open until they happen.

The Game Visual Debugging and Game Development Studio skills were consulted.
Their `game-dev` CLI is absent in this environment, so no sealed Game Development
Studio run or provider receipt is claimed. Existing Blender capture records and
the local Pillow contact sheet remain ordinary project evidence.

## Clay silhouette command

`npm run qa:clay` produces side/front/rear/top/front34/rear34 with neutral material
and zero energy. Compare against the primary board before details.
