# Sketch to Furniture — portable plugin

Version 0.2.0. Source and full documentation: https://github.com/plamen911/sketch-to-furniture

The workflow is in [skills/sketch-to-furniture/SKILL.md](skills/sketch-to-furniture/SKILL.md).
A compatible ChatGPT/plugin host must provide file and Python execution. Packaging does not add tools or remove plan limits.

To run the included example locally:

```bash
cd skills/sketch-to-furniture
python3 -m pip install -r requirements-render.txt  # optional PNG rendering
python3 scripts/furniture.py examples/wardrobe/project.json --out projects/wardrobe/preview
```

Open the generated index.html, or review exterior.png/interior.png when Pillow is available.
All plans remain preliminary until the craftsperson verifies manufacturing decisions.

Author: Plamen Markov — https://plamen.lynxlake.org/
MIT license. Customer source photos and conversations are not included.
