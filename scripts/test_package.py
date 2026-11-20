#!/usr/bin/env python3
"""Check that the built plugin executes independently from its development checkout."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = (ROOT / "VERSION").read_text().strip()
    archive = ROOT / f"dist/sketch-to-furniture-v{version}.zip"
    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="package-", dir=work) as tmp:
        folder = Path(tmp)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert not name.startswith("/") and ".." not in Path(name).parts
            z.extractall(folder)
        skill = folder / "skills/sketch-to-furniture"
        output = folder / "result"
        subprocess.run(
            [
                sys.executable,
                str(skill / "scripts/furniture.py"),
                str(skill / "examples/wardrobe/project.json"),
                "--out",
                str(output),
            ],
            check=True,
            cwd=folder,
        )
        report = json.loads((output / "validation.json").read_text())
        assert report["part_count"] == 28 and report["board_count"] == 4
        assert (output / "index.html").is_file()
        assert (
            json.loads((output / "materials-cost.json").read_text())["client_total_eur"]
            is None
        )
        for name in (
            "model.dae",
            "model.obj",
            "cutting.pdf",
            "drawing.svg",
            "parts.csv",
            "package.zip",
        ):
            assert (output / name).stat().st_size > 0
        print(
            "Portable plugin executes from a fresh extracted folder; private source photo is absent."
        )


if __name__ == "__main__":
    main()
