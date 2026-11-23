#!/usr/bin/env python3
"""Build a portable skills-only plugin and a plain ChatGPT instruction bundle."""

import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
RUNTIME_FILES = [
    "furniture.py",
    "project_review.py",
    "project_history.py",
    "test_project_history.py",
    "test_project_review.py",
    "costing.py",
    "render_preview.py",
    "make_wardrobe.py",
    "test_furniture.py",
    "test_costing.py",
]


def check_package(folder):
    manifest = json.loads((folder / "plugin.json").read_text())
    assert manifest["name"] == "sketch-to-furniture"
    skill = folder / "skills/sketch-to-furniture"
    entry = (skill / "SKILL.md").read_text()
    assert re.search(r"^name: sketch-to-furniture$", entry, re.M)
    for path in re.findall(r"\]\((references/[^)]+)\)", entry):
        assert (skill / path).is_file(), path
    for path in skill.rglob("*"):
        assert not path.is_symlink(), path
        if path.is_file() and path.suffix in (".md", ".json", ".py", ".html", ".txt"):
            text = path.read_text()
            assert "chatgpt.com/share/" not in text, path
            assert "/Applications/MAMP/" not in text, path
    assert not list(skill.rglob("source.jpeg"))
    return manifest


def build():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    folder = dist / "plugin"
    if folder.exists():
        shutil.rmtree(folder)  # only generated distribution path
    skill = folder / "skills/sketch-to-furniture"
    skill.mkdir(parents=True)
    shutil.copyfile(ROOT / "VERSION", skill / "VERSION")
    text = (ROOT / "SKILL.md").read_text()
    text = text.replace(
        "For this development task that is `/Applications/MAMP/htdocs/ai/skills/sketch-to-furniture/`. ",
        "",
    )
    (skill / "SKILL.md").write_text(text)
    for name in ("assets", "references", "pricing", "evals", "examples"):
        shutil.copytree(
            ROOT / name,
            skill / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    (skill / "scripts").mkdir()
    for name in RUNTIME_FILES:
        shutil.copyfile(ROOT / "scripts" / name, skill / "scripts" / name)
    shutil.copyfile(ROOT / "requirements-render.txt", skill / "requirements-render.txt")
    (folder / "README.md").write_text(f"""# Sketch to Furniture — portable plugin

Version {VERSION}. Source and full documentation: https://github.com/plamen911/sketch-to-furniture

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
""")
    shutil.copyfile(ROOT / "LICENSE", folder / "LICENSE")
    if (ROOT / "docs/images").exists():
        shutil.copytree(ROOT / "docs/images", folder / "docs/images")
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "sketch-to-furniture",
        "version": VERSION,
        "description": "Turn photographed furniture sketches into reviewable CAD, material previews, cutting plans and sourced material estimates.",
        "author": {"name": "Plamen Markov", "url": "https://plamen.lynxlake.org/"},
        "repository": "https://github.com/plamen911/sketch-to-furniture",
        "license": "MIT",
        "keywords": ["furniture", "cad", "cutting", "agent-skills"],
        "extensions": {
            "com.openai": {
                "interface": {
                    "displayName": "Sketch to Furniture",
                    "shortDescription": "Furniture sketches to CAD, previews and cutting plans",
                    "developerName": "Plamen Markov",
                    "category": "Productivity",
                    "websiteURL": "https://plamen.lynxlake.org/",
                }
            }
        },
    }
    (folder / "plugin.json").write_text(json.dumps(manifest, indent=2))
    marketplace = folder / ".agents/plugins"
    marketplace.mkdir(parents=True)
    (marketplace / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "sketch-to-furniture",
                "interface": {"displayName": "Sketch to Furniture"},
                "plugins": [
                    {
                        "name": "sketch-to-furniture",
                        "source": {"source": "local", "path": "./"},
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": "Productivity",
                    }
                ],
            },
            indent=2,
        )
    )
    hashes = {
        str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }
    (folder / "files.sha256.json").write_text(json.dumps(hashes, indent=2))
    check_package(folder)
    archive = dist / f"sketch-to-furniture-v{VERSION}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                z.write(path, str(path.relative_to(folder)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    print(
        json.dumps(
            {"archive": str(archive), "version": VERSION, "files": len(hashes)},
            indent=2,
        )
    )


if __name__ == "__main__":
    build()
