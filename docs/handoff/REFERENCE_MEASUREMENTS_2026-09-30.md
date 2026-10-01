# Exact reference measurements — 2026-09-30 pass9

These measurements come from the user's three exact uploaded reference images and supersede the earlier pass8 collage wherever the images disagree. They are proportion constraints, not claims about real-world TRON production dimensions.

## Source fingerprints

- tail/rear view upload `ref_front.jpg`: 1024×994, SHA-256 `ef6736245807d6bee154d39ee9ed3eb420da991abbc9917fb5099cb66250209d`
- handlebar/front view upload `ref_rear.jpg`: 819×1024, SHA-256 `793dd453fe5705bfceed0c9bcad2efd2f77165ea1453e1e542d0ccc2ef3fcce6`
- side view upload `ref_side.png`: 1024×341, SHA-256 `ed62b4f72ab0a525a0f329c93a677f18d5772a464c83007b2214b52e9d3d8ca2`

## Measured design contract

The side view's wheel centers are about 705 px apart while the visible outside wheel diameter is about 300 px, giving wheelbase / wheel diameter ≈ 2.35. With the retained 0.92 m outside diameter, pass9 uses a 2.16 m wheelbase. The full visible side silhouette is about 3.36 wheel diameters, giving a target overall length around 3.10 m.

The white hub opening is only about 112 px across against ~300 px outer diameter, so hub-void / wheel-diameter ≈ 0.37. Pass8 used 0.54 / 0.92 ≈ 0.59 and therefore could not match the reference's massive thick wheel annulus. Pass9 uses a 0.35 m hub void while retaining hubless architecture, named wheel nodes, pivots and animation ownership.

The end views show much more lateral wheel mass and a much broader vehicle than pass8. Pass9 uses ~0.42 m front and ~0.48 m rear wheel sections, a ~0.74 m visual body width, and a ~0.72 m grip-to-grip target (±0.36 m) while keeping solved rider X/Z contacts.

The exact front view requires a broad faceted cowl above the tire with two dominant vertical energy rails and wide handlebars. The exact rear view requires a broad rear tire presentation, sculpted shoulders, an open polygonal structural hoop above it, and a centered vertical rear energy blade. The side view requires huge wheel masses, a low continuous center body, a framed reactor and bodywork that visibly wraps both wheels.

## Orientation note

The repo uses nose/front = -X. The supplied side reference shows the front on image-right, so direct side overlays must horizontally mirror the reference (or compare front/rear landmarks by identity) before judging longitudinal placement. This is why the reactor remains rear-of-center in repo coordinates rather than being incorrectly moved to the opposite half.

## Visual gate

Do not accept CI alone. Fresh pass9 side/front/rear/top clay and lit/lights-off renders must be compared against these three exact images. Any render that preserves the old thin wheel annulus, narrow end-on stance, missing front cowl, or missing rear hoop is a failed visual gate even if validators pass.
