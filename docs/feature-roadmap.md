# Ideas assessed from comparable tools

Reviewed on 2026-11-23. Borrow interaction principles, not vendor code or assets.

## Implemented in 0.4.0

- Visible stages backed by generated output: distinguish prepared, partial and pending; never treat a counter as manufacturing approval. Inspired by the user's Srezio screenshots.
- Dedicated assumptions section, linked directly from the viewer and stages.
- Toggleable model dimensions and optional internal clearances derived from actual panel faces.
- Selected-part card: finished/raw sizes, thickness and local-edge diagram. Extends our existing part highlighting; useful for workshop checks.

## Implemented in 0.5.0

- Source-to-model dimension table with explicit provenance/status and automatic mismatch detection.
- Revision snapshots and explicit comparison of parts, materials, fittings, stock counts and priced material subtotals.
- Display-only exploded panel view with within-version numbers and a number-to-part CSV.

## Design rationale for these additions

1. Source-linked dimension review table: written value, interpretation, source and confirmation status. Inspired by [AnyCutlist's review workflow](https://www.anycutlist.com/). Prefer explicit provenance over invented numerical confidence scores.
2. Revision comparison: show changed dimensions, parts, sheet count and material subtotal between saved builds. [Srezio](https://srez.io/) advertises history and connected downstream updates; our snapshots need explicit regeneration rather than silently stale exports.
3. Group isolation and exploded assembly views: reveal selected components and numbered parts. [OpenCutList](https://docs.opencutlist.org/features/parts) documents configurable exploded views. Our current interior view hides fronts; it is not a hinge or assembly simulation.
4. Workshop labels and reusable offcut inventory: associate each cut piece with the same part ID in CAD, cut list and label; price purchased material separately from reused inventory.

## Defer until field evidence supports it

Free dragging/resizing panels in-browser, CNC postprocessors, automated drilling, AR and autonomous agents. These require dependable construction rules and meaningful tests; adding a button without recomputing geometry, cuts and prices would reduce trust. Field-test unseen sketches before expanding the CAD editor.
