#!/usr/bin/env python3
"""Build a shareable static demo from the sanitized example, never client uploads."""

import json
from pathlib import Path
import shutil
import sys
import furniture

ROOT = Path(__file__).resolve().parents[1]


def main():
    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    source = work / "public-demo.json"
    project = json.loads((ROOT / "examples/wardrobe/project.json").read_text())
    assert not project.get("source_image") and not project.get("source_conversation")
    project["name"] = "Примерен гардероб с две чекмеджета"
    project["subtitle"] = "Демо на Sketch to Furniture · 1200 × 2200 × 600 mm"
    project["demo"] = True
    source.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    target = ROOT / "dist/demo"
    if target.exists():
        shutil.rmtree(target)  # generated demo only
    furniture.build(source, target)
    (target / ".nojekyll").write_text("")
    # Public demo must not contain uploaded customer imagery or discussion URLs.
    assert not list(target.glob("source.*"))
    assert "chatgpt.com/share/" not in (target / "index.html").read_text()
    print("Built sanitized demo at " + str(target))


if __name__ == "__main__":
    main()
