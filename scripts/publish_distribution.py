#!/usr/bin/env python3
"""Publish generated plugin files to a fast-forward-only distribution branch in CI."""

import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This publisher runs only in GitHub Actions.")
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    api = "https://api.github.com/repos/" + repo

    def request(method, path, payload=None, missing=False):
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(api + path, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if missing and error.code == 404:
                return None
            raise RuntimeError(
                f"GitHub API {method} {path}: HTTP {error.code}"
            ) from None

    folder = ROOT / "dist/plugin"
    from package_skill import check_package

    check_package(folder)
    ref = request("GET", "/git/ref/heads/distribution", missing=True)
    parent = ref["object"]["sha"] if ref else None
    tree = []
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            blob = request(
                "POST",
                "/git/blobs",
                {
                    "content": base64.b64encode(path.read_bytes()).decode(),
                    "encoding": "base64",
                },
            )
            tree.append(
                {
                    "path": str(path.relative_to(folder)),
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob["sha"],
                }
            )
    result = request("POST", "/git/trees", {"tree": tree})
    if parent:
        previous = request("GET", "/git/commits/" + parent)
        if previous["tree"]["sha"] == result["sha"]:
            print("Distribution is already current.")
            return
    commit = request(
        "POST",
        "/git/commits",
        {
            "message": "Build plugin from " + os.environ.get("GITHUB_SHA", "source"),
            "tree": result["sha"],
            "parents": [parent] if parent else [],
        },
    )
    if parent:
        request(
            "PATCH",
            "/git/refs/heads/distribution",
            {"sha": commit["sha"], "force": False},
        )
    else:
        request(
            "POST",
            "/git/refs",
            {"ref": "refs/heads/distribution", "sha": commit["sha"]},
        )
    observed = request("GET", "/git/ref/heads/distribution")
    assert observed["object"]["sha"] == commit["sha"]
    print("Updated https://github.com/" + repo + "/tree/distribution")


if __name__ == "__main__":
    main()
