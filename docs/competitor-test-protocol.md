# Comparative test protocol: photo to workshop

Date: 2026-11-23. Case: wardrobe-001. Products: Sketch to Furniture 0.3.1, Srezio, Coobic.

## Separate the two tests

**A — blind interpretation:** give each assistant the same photo and the same short request. Record the first transcription, missing dimensions, questions, corrections and time until a useful preview. Do not give the expected answer in advance.

**B — reviewed specification:** provide the same reconciled dimensions, materials and preliminary construction choices to each tool. Check the actual model and exported files rather than a chat assertion. This isolates modeling/manufacturing from handwriting recognition.

Our reference wardrobe has already been used to develop the plugin. Its output is a known-case regression, not an independent accuracy benchmark. Future unseen sketches are necessary to establish generality. Different joinery may legitimately change the number of parts; do not rank products by matching our 28-part implementation alone.

## Common specification for stage B

All values in mm. Overall W1200/H2200/D600 including fronts and back, excluding handles. Two nominal 600 bays; white particleboard 18 carcass, cream matte AGT 730A MDF 18 fronts, overlaid HDF 3 back, 100 plinth. Left: two nominal 200 drawer-front bands, door above, three shelves with equal clear openings. Right: two lower shelves with equal clear openings and a 1100 clear hanging zone measured from upper shelf top to top underside, not to rail axis.

Provisional construction: sides enclose bottom/top; 2 mm front gaps; front banding 1 mm on all four edges. Carcass banding and exact hardware remain unconfirmed. Particleboard stock X2800/Y2070, MDF X2800/Y1220, 20 trim from each edge, 4 kerf, primary cuts parallel Y. Material cost only; no invented prices; labor/profit/client selling total unfilled.

## Independent checks

- Under the declared 18 mm two-bay assembly, clear bay width is (1200-3*18)/2 = 573.
- Current nominal vertical bands are 100+200+200+1700 = 2200; they are not raw front sizes.
- Under the stated front gap convention, finished fronts are 597x1696 (left), 597x2096 (right), 597x198 (each drawer); with 1 mm bands on four edges, raw sizes are 595x1694, 595x2094 and 595x196. A different gap allocation must be disclosed and assessed rather than silently treated as equivalent.
- Shelf spacing means clear openings; hanging clear height must actually measure 1100.
- Depth chain closes at 600 with front/back included; handle protrusion is separate.
- Cut list and model use the same parts, thicknesses, bands and grain; no omitted or overlapping cut pieces.
- HDF without a declared stock format cannot be included in a complete purchased-sheet claim.
- Missing prices stay missing; a material subtotal is not a selling quote.

## Evidence to retain

Save the exact request, product version/model when visible, prompts/answers, downloaded files, screenshots, wall-clock times and corrections. Keep original photo, account information and competitor project URLs privately under projects/. Publish only summarized observations with source URLs.

For every criterion use one of: checked/pass, checked/fail, vendor claim only, not tested, blocked. Do not replace blocked/not tested with failure or invent a percentage score. A timeout in one session is not evidence that a product never works.

## Public sources

- Srezio: https://srez.io/ and https://srez.io/editor
- Coobic: https://coobic.co/ and https://coobic.co/design

Supplier and account restrictions are time-sensitive. Record what was visible on the observation date. No purchases, paid upgrades or account registration are part of this test.
