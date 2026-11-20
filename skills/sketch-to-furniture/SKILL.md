---
name: sketch-to-furniture
description: Reconstruct dimensionally accurate furniture from photographed sketches; create editable SketchUp-compatible 2D/3D models, material-aware cut lists, panel nesting, A4 cutting layouts and geometry-based material previews.
---

# Furniture CAD and panel cutting workflow

## When to use
Use for a photographed hand sketch of furniture requiring accurate 2D/3D CAD, SketchUp interoperability, materials, bill of parts, board nesting, print-ready A4 cutting plans, and sharing deliverables.

## Start here
- For new preliminary projects, read [references/stoyan-profile.md](references/stoyan-profile.md) and its provisional JSON defaults. The user authorized reasonable assumptions for preparation; explicit project answers override them. Record assumptions, never invented confirmations.
- Read [references/stoyan-workflow.md](references/stoyan-workflow.md) for the photo-first on-site workflow, minimal-choice questions and material-only pricing scope.
- Read [references/project-format.md](references/project-format.md) before compiling project data. Use [references/client-sketch-style.md](references/client-sketch-style.md) as evidence about this client's drawing conventions, not as universal rules.
- See [references/platforms-and-sync.md](references/platforms-and-sync.md) for web/desktop/mobile distribution and the unverified Free-plan acceptance target. Never promise that a ZIP installs tools or connects GitHub automatically.

## Preferred Bulgarian supplier sources
- Start material, decor, texture, hardware and price research with **Kedar** (https://www.kedar-ood.com/) and **ROSI** (https://rosi.bg/bg), as requested by the user. Consult other sources only when the needed information is missing or requires a manufacturer cross-check.
- Match exact manufacturer/finish code, thickness, sheet format, edge-band size and hardware SKU. Keep supplier samples and prices attributed to the matching variant; do not substitute a nearby cream or white decor silently.
- Record the direct product URL and observation date. Missing public prices remain unquoted. A failed page fetch is not evidence of missing stock or price; use the accessible supplier page or report the verification limit.

## Implementation and project files
- Maintain source changes only in the user's selected checkout. In a packaged/cloud run, resolve scripts, assets and references relative to this SKILL.md and generate files in the host's writable workspace. Do not claim access to the author's Mac from a phone chat.
- The assistant reads the sketch and reconciles answers, then writes explicit project JSON. The generator does not perform OCR or autonomously infer joinery.
- Run `python3 scripts/furniture.py <project.json> --out <new-output-folder>` from the skill directory. The generator refuses to overwrite existing output folders.
- `scripts/furniture.py` validates geometry, calculates band-adjusted raw dimensions, compares four guillotine-strip nesting candidates and exports CAD, cut lists, PDF/SVG plans, validation data and a self-contained viewer. Proven lower bounds distinguish minimum board counts from heuristic results.
- The core requires Python 3.10+ and its standard library. `scripts/render_preview.py` optionally uses Pillow to produce exterior.png/interior.png for inline delivery in mobile chats. If unavailable, say so and offer the HTML viewer's PNG export; do not imply an image file was produced.
- `scripts/costing.py` writes a material-only estimate using dated supplier observations and explicit missing/provisional lines. Browse and update the selected variants before presenting current prices. Labor, profit and final selling price remain unfilled unless the user later changes this scope.
- `scripts/make_wardrobe.py` rebuilds only the reviewed reference example. It is not a universal cabinet rule. Private real-project files are under `projects/`; sanitized public examples are under `examples/`.
- `assets/viewer.html` supports orbit, zoom, hidden fronts, color trials, part highlighting and PNG/parameter export. Color trials do not rewrite the CAD exports; regenerate from the downloaded parameters.
- Test with `python3 scripts/test_furniture.py` and `python3 scripts/test_costing.py`. All outputs remain preliminary until the craftsperson verifies joinery, hardware, banding and production tolerances. Materials without a stock format remain in the model/CSV and are explicitly excluded from nesting.

## Principles
- Treat handwritten dimensions as unverified until read and reconciled. Never invent dimensions without marking assumptions.
- Use millimetres as the model's actual units at 1:1; drawing print scale is separate.
- Keep outer cabinet dimensions, clear internal dimensions, part dimensions, front gaps, back panel, hinges and drawer hardware distinct.
- Ask focused questions for ambiguous layout, dimensions, thickness, material and hardware. Avoid repetitive confirmations once answered.
- Validate that all vertical and horizontal dimension chains close. Explicitly distinguish nominal module widths from internal clear widths.
- Before calling any plan production-ready, verify joinery, cutting tolerances, edge banding, grain direction, drawer slides, hinge clearances and material thicknesses.

## Intake and specification
1. Inspect the uploaded sketch. Transcribe every legible dimension and component with confidence/ambiguity flags.
2. Establish overall width, height, depth; cabinet carcass and back thickness; front thickness; shelves, hanging rail and drawers.
3. Confirm what distances mean: e.g. hanging-zone clear height from upper surface of shelf to underside of upper limit; rail axis is a separate measurement.
4. Confirm whether shelf spacing means equal *clear* spaces or equal shelf centerline spacing.
5. Confirm finishes separately for carcass, fronts and back. Manufacturer finish codes should not be represented as exact texture unless a verified source is supplied.

## 2D and 3D outputs
- Generate dimensioned 2D DXF and an editable 3D exchange model such as COLLADA DAE (SketchUp import) or OBJ/GLB where suitable. Do not claim a native SKP unless actually produced.
- Model individual panels and fronts as named independent components, with materials assigned by part; provide a structured part schedule and metadata (position, size, material, thickness, edge treatment).
- Keep drawing/model geometry dimensionally consistent. Verify bounding boxes and a sample of components programmatically.
- Include a readable assumptions/verification file, plus a short SketchUp import guide.

## Project visualization with selected finishes
- Include a realistic preview of the furniture using the project's selected colors, materials, edge finishes and visible hardware, alongside the technical drawings and cutting layouts.
- Build the preview from the same dimensionally verified geometry and part/material assignments used for the CAD model and cut list; keep changes synchronized across these outputs.
- Provide an exterior perspective with fronts closed and an interior view with fronts open or hidden so the internal layout can be assessed. Add detail views when needed to show a finish or construction choice.
- Use manufacturer textures or user-supplied samples when available. Identify approximate textures and colors explicitly; a finish code alone does not establish an exact visual match. Lighting, display and texture scale affect appearance, so the preview is not a physical color sample.
- Keep material/finish choices explicit for carcass, fronts, back and edges. Ask only for missing choices that materially affect the requested preview; label provisional choices on preliminary images.
- If an AI-generated image is used for atmosphere or styling, label it as illustrative and check it against the CAD geometry. It must not replace the geometry-based preview or serve as evidence of dimensional or manufacturing accuracy.

## Cutting / nesting
1. Create a manufacturing cut list: unique part ID, name, count, length, width, thickness, material, edge banding sides, grain orientation, allowance, and note.
2. Ask what '20 mm trimming' means. For preliminary plans the provisional profile may supply 20 mm from each edge, explicitly marked unconfirmed; production requires confirmation. This is board-edge trimming, NOT edge banding.
3. Set saw kerf (e.g. 4 mm) only as an explicitly declared parameter; maintain separation between pieces.
4. Board sizes and axes are parameters. Preserve the requested orientation exactly. Example initial orientation: carcass X=2070,Y=2800; fronts X=1200,Y=2800. Rotated: carcass X=2800,Y=2070; fronts X=2800,Y=1200.
5. 'Cut along Y' means primary rip cuts are parallel to Y. Re-orient nesting/strip segmentation accordingly; changing axis labels alone is insufficient.
6. Respect grain direction and no-rotation constraints. If rotation is allowed, mark rotated parts. Check fit and overlaps; show yield and waste and number of boards.
7. Provide one A4 PDF page per board (landscape or portrait as needed), with full board outline, trim zone, axis arrows, rip-cut lines, part IDs, dimensions, material, kerf, legend, and a clear NOT-FOR-PRODUCTION caveat if unresolved details remain.
8. Supply machine-editable DXF/SVG plus CSV parts list and a ZIP package; validate each generated file exists before sharing links.

## Reference project decisions (example only; never apply automatically to a new project)
- Wardrobe outer dimensions: 1200 W × 2200 H × 600 D mm.
- Carcass: white 18 mm particleboard; back: white 3 mm HDF; fronts: cream AGT 730A MDF (exact color/texture unverified).
- Left: 3 shelves, equal clear spacing, 2 stacked drawers each nominally 200 mm tall, left door above drawers.
- Right: 2 lower shelves, equal clear spacing, hanging zone 1100 mm clear height measured from shelf top to upper boundary underside, right door covering full carcass height above plinth.
- Plinth nominal 100 mm. Earlier dimensions 1700 + 200 + 200 + 100 = 2200 mm are nominal vertical bands; verify actual construction and gaps before manufacturing.
- Carcass sheet 2800×2070 mm, front sheet 2800×1220 mm (latest confirmed choice); trim 20 mm each board edge (if confirmed); kerf 4 mm.
- Both original and rotated axis layouts have been discussed; use the user's **latest explicit instruction** for current output.

## Sharing and delivery
- Verify actual files, not merely file names or historical sandbox references.
- When emailing, attachments can be blocked by recipient policies even after Gmail reports SENT. Check delivery status notices. Prefer separate PDFs and CAD attachments rather than ZIP containing scripts if recipient rejects it; do not claim successful delivery without confirmation.
- Store the reusable skill instructions as SKILL.md and use them as the starting checklist for future projects. A saved file in Library is not automatically an installed ChatGPT plugin skill.

## Mandatory edge-banding confirmation (user rule)
- Before finalizing a manufacturing cut list, resolve whether each relevant panel needs edge banding (кантиране), reusing prior confirmed answers. A preliminary on-site preview may defer this with explicit assumptions; do not treat unmentioned parts as intentionally unbanded.
- Confirm **which exact edges of each part** receive banding: long/short, left/right/top/bottom, front/back as viewed in the installed orientation. For ambiguous orientation, include a labeled part sketch or table.
- Confirm edge-band material, thickness, finish/color, and whether the stated dimensions are finished dimensions or raw cut sizes.
- Calculate cut sizes accounting for band thickness on the specified edges only; separately list finished dimensions, raw dimensions, edge lengths, quantities, and any allowance for trimming/production.
- Do not finalize production cutting layouts before this is resolved. If user wants a preliminary plan, clearly mark unresolved banding as a pending assumption.

## Edge-band thickness selection — mandatory UI rule
- Standard thickness choices are **0.8 mm**, **1 mm**, and **2 mm**.
- When asking the user to specify band thickness, always offer these three as a **selectable list / single-choice control**; do not require free-text entry.
- For multiple parts, confirm which exact edges are banded separately from thickness. Do not infer banding from the thickness choice alone.
- For preliminary projects the user-authorized provisional profile may supply a thickness with explicit assumption status. Final manufacturing still requires exact edge confirmation.

## Standard stock sheet formats — mandatory selection UI
- Particleboard (ПДЧ): **2800 × 2070 mm**, **2800 × 2100 mm**.
- MDF (МДФ): **2800 × 1220 mm**, **2800 × 2070 mm**, **2800 × 1300 mm**.
- When a stock format is unresolved for production, ask the user to choose a stock sheet size from a selectable list (radio/select), filtered by material. Do not require typing these standard sizes.
- A preliminary layout may use the provisional profile without another question; label it unconfirmed. These are nominal stock dimensions, not usable cutting areas: apply independently confirmed perimeter trimming and saw kerf.
- Keep stock dimensions separate from axis orientation, rotation/grain constraints, and panel thickness.
- For existing layouts, preserve the explicitly selected stock dimensions until the user confirms a change. The reference wardrobe's former 2800 × 1200 mm MDF sheet is a historical assumption, not one of the newly provided standard MDF options; use the subsequently confirmed 2800 × 1220 mm for this wardrobe.

## Public project gallery
See [references/public-gallery.md](references/public-gallery.md). The gallery builds only explicitly listed sanitized projects; a ChatGPT upload does not itself publish anything.
