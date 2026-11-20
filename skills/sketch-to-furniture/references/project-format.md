# Project format and generation

All maintained code, project inputs and generated revisions live in this skill directory. Python 3.10+ and its standard library are sufficient for the core exports and interactive viewer. Optional PNG rendering uses Pillow from requirements-render.txt.

## From a sketch to files

1. Read the image visually and consult the client's answers. Record confirmed dimensions separately from construction assumptions; do not treat an assistant's earlier assumption as a client's confirmation.
2. Compile explicit panels into a JSON project using the format below. Place the original image and project-specific notes together under `projects/<project-name>/`. Derive each panel from the construction, rather than scaling pixels in the photograph.
3. Run `python3 scripts/furniture.py projects/<project-name>/project.json --out projects/<project-name>/<new-revision>` from the skill directory.
4. Read `validation.json`, visually inspect the 3D model and cutting pages, and compare dimension chains to the sketch. If revising inputs, use a new output folder. Existing output folders are never overwritten.

## Root fields

- `schema_version`: 1. `units`: `mm`. `name`: project title. `subtitle`: optional description.
- `source_image`: optional image filename relative to the input JSON, e.g. `source.jpeg`. It must stay inside the input project folder. The generator copies it into the output so the ZIP includes the original sketch. The input image is not interpreted by Python.
- `source_conversation`: optional provenance URL. `confirmed`: list of confirmed decisions. `assumptions`: list of unresolved or provisional choices. These are shown in the viewer and copied into the report.
- `design_bounds_mm`: optional `{"min":[0,0,0],"max":[1200,600,2200]}`. Describes the furniture envelope excluding protruding handles; does not rescale parts. `validation.json` also reports actual geometry bounds including fittings.
- `materials`: map of material ID to material specification. `parts`: one record for each physical panel. Repeated panels use separate unique IDs.
- `fittings`: optional schematic boxes or cylinders. They are exported in CAD and shown in the viewer but excluded from panel nesting and manufacturing lists.

## Materials

Required: `name`, `kind` (`particleboard`, `mdf`, `hdf`, etc.), `thickness_mm`, `color` (`#RRGGBB`). `finish_note` explains approximation or manufacturer reference.

`stock` is either `null` (explicitly excluded from nesting) or an object with `x_mm`, `y_mm`, `trim_mm`, `kerf_mm`, `primary_axis` (`X` or `Y`). Trim applies to each of four edges, kerf is the separation between pieces. A zero kerf is rejected. Use the standard sheet formats in SKILL.md; nonstandard particleboard or MDF requires `custom_format_confirmed: true`.

Primary axis describes the direction of the full strip cuts. It is independent of stock grain: when grain is specified, grain follows sheet Y. If the physical stock grain runs along X, change the coordinate specification or extend the schema explicitly; do not relabel only the drawing.

## Panels

```json
{
  "id": "DOOR_R",
  "name": "Дясна врата",
  "origin_mm": [601, 0, 102],
  "size_mm": [597, 18, 2096],
  "panel_axes": [0, 2],
  "material": "cream",
  "group": "front",
  "bands_mm": {"u0": 1, "u1": 1, "v0": 1, "v1": 1},
  "grain": "none",
  "allow_rotation": true
}
```

Coordinates: X right, Y rearward, Z up; a front view looks in the positive Y direction. `origin_mm` is the minimum corner. `size_mm` is the **finished envelope after banding**, along X/Y/Z. `panel_axes` identifies U and V; the remaining dimension must match the material thickness. Above, U is X and V is Z.

`bands_mm` must explicitly specify all four edges, using 0, 0.8, 1 or 2 mm. U0/U1 are the edges at minimum/maximum U (and run along V); V0/V1 are at minimum/maximum V (and run along U). Raw U = finished U - U0 - U1, and likewise V. Thickness itself is not changed. Zero represents a modeling value, not evidence of user confirmation. Record provisional zeros in assumptions.

`group` is one of `carcass`, `front`, `back`, `shelf`, `drawer`, `plinth`. The interior view hides `front` panels; no door motion is simulated.

`grain` is `none`, `u` or `v`. For a constrained grain axis, that panel axis must follow stock Y; 90-degree rotation is used only when explicitly allowed. If no permitted orientation fits, generation fails with the part ID.

## Fittings

A fitting requires unique `id`, `name`, `origin_mm`, `size_mm`, and `color`. `shape` defaults to `box`; `cylinder` also requires axis 0, 1 or 2. Its cylinder fits the given bounding box. `hide_with_fronts: true` hides handles in the interior view. Fittings may intentionally touch/intersect panels; the solid-overlap validator applies to panels only. Actual hardware requires separate engineering verification.

## Outputs and limits

- `index.html`: embedded data, local Canvas 3D renderer with per-pixel depth buffer; no network libraries. Flat-lit approximate material colors, not a photorealistic finish simulation. PNG export captures the current view. No manufacturer texture upload is implemented in v0.2.
- `model.dae`: COLLADA 1.4.1, millimeter unit, Z-up, separate named geometries and materials. `model.obj` + `model.mtl`: finished panels/fittings, coordinates in mm. Actual SketchUp import must still be checked on the user's version. No native SKP.
- `drawing.dxf` / `drawing.svg`: front, side and top orthographic panel outlines with overall dimensions. Hidden outlines are included schematically; these are not workshop drilling/joinery drawings. DXF coordinates are 1:1 mm.
- `parts.csv`: every panel, finished/raw U/V, thickness, per-edge band thickness, nominal band length, grain. CSV is UTF-8 with BOM. Band lengths have no added waste allowance.
- `layout.json`, per-board SVG, `cutting.dxf`, `cutting.pdf`: raw panel sizes, trim, kerf, orientation, primary strips. PDF uses landscape A4 with ASCII part IDs. Board count includes only materials with stock formats.
- `validation.json`: checks, actual bounds, excluded parts, warnings and project assumptions. `manifest.json`: file checksums. `package.zip`: generated outputs; the original image is included when source_image is specified.

The deterministic strip heuristic produces a feasible arrangement with kerf clearance; it is not a nesting optimizer. It does not output CNC toolpaths or an execution order for every cut. Finished sizes, offsets and raw sizes come from one explicit panel model; assemblies with curved/angled panels, milled profiles and nonrectangular pieces are outside v0.2.
