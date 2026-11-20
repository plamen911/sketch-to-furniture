#!/usr/bin/env python3
"""One-way source update: refuse local changes, then fetch and fast-forward only."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(*args, capture=False):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, text=True, capture_output=capture
    )


def main():
    if not (ROOT / ".git").exists():
        raise SystemExit("Not a source checkout. Download the latest release instead.")
    if git("status", "--porcelain", capture=True).stdout.strip():
        raise SystemExit(
            "Local changes detected. Commit or resolve them before updating; nothing was overwritten."
        )
    branch = git("branch", "--show-current", capture=True).stdout.strip()
    if branch != "main":
        raise SystemExit(
            "Automatic source update is limited to main. Review the current branch manually."
        )
    remote = git("remote", "get-url", "origin", capture=True).stdout.strip()
    if remote not in (
        "https://github.com/plamen911/sketch-to-furniture.git",
        "git@github.com:plamen911/sketch-to-furniture.git",
    ):
        raise SystemExit("Unexpected origin. Review it manually before fetching.")
    git("fetch", "origin", "main")
    git("merge", "--ff-only", "origin/main")
    print(
        "Source checkout is current. Installed plugins and uploaded ZIPs are separate copies."
    )


if __name__ == "__main__":
    main()
