# Portfolio description

## Short

Sketch to Furniture is an AI-assisted workflow that converts photographed furniture sketches into reviewed CAD models, material previews, cutting plans and sourced material estimates. It combines visual interpretation and focused clarification with deterministic geometry, nesting and pricing checks.

## Project case study

An experienced cabinetmaker sketches furniture on paper while discussing it with the customer. I designed an assistant workflow around that existing behavior: photograph the sketch, reconcile dimensions with a few concrete choices, show a geometry-based preview, and carry the same panel data into workshop preparation.

The AI handles interpretation; Python owns geometry, raw-size calculations, nesting and arithmetic. The implementation exports editable DAE/OBJ, DXF/SVG drawings, A4 cutting plans and an interactive browser viewer. Material estimates preserve exact supplier variants, units, VAT basis and observation dates, while leaving missing costs explicit.

A reviewed wardrobe is the first evaluation case. More complex field tests, mobile delivery and the personal ChatGPT Free installation path remain to be verified. The repository includes regression tests and an improvement protocol rather than unmeasured accuracy or time-saving claims.

Source: https://github.com/plamen911/sketch-to-furniture
