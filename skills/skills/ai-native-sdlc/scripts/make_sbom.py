#!/usr/bin/env python3
"""make_sbom.py — emit a CycloneDX 1.5 SBOM for the gate.

The gate is stdlib-only, so a conventional dependency SBOM would be nearly empty and
would say nothing useful. What a consumer actually needs to know is *which files carry
the policy logic and what each one hashes to*, because those files decide whether a
change may merge. So each file becomes a component with its own SHA-256, and the tool
that produced the SBOM is recorded.

CycloneDX rather than SPDX because CycloneDX's file-level components and hash fields fit
a script bundle directly, and it is the format most CI scanners ingest natively.

Stdlib only, so it runs anywhere the gate runs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

# Files whose contents constitute the enforcement logic. Anything outside this list is
# documentation and does not change a merge decision.
INCLUDE_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".json", ".md"}
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", "node_modules"}


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root: pathlib.Path) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix not in INCLUDE_SUFFIXES:
            continue
        out.append(p)
    return out


def build(root: pathlib.Path, name: str, version: str) -> dict:
    files = collect(root)
    if not files:
        raise SystemExit(f"make_sbom: no candidate files under {root}")

    components = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        components.append(
            {
                # 'file' is the correct CycloneDX type for a source artifact that is not a
                # separately-versioned library.
                "type": "file",
                "bom-ref": rel,
                "name": rel,
                "version": version,
                "hashes": [{"alg": "SHA-256", "content": sha256_of(f)}],
            }
        )

    # Timestamp is UTC and second-resolution; it is metadata, not part of any hash, so it
    # does not affect the reproducibility of the artifact itself.
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": [{"vendor": "ai-native-sdlc", "name": "make_sbom.py", "version": "1"}],
            "component": {
                "type": "application",
                "bom-ref": name,
                "name": name,
                "version": version,
                "description": (
                    "Deterministic SDLC stage gate. Grants or refuses merge authority, so "
                    "each component hash below is security-relevant."
                ),
            },
        },
        "components": components,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Directory to inventory")
    ap.add_argument("--name", default="ai-native-sdlc-gate")
    ap.add_argument("--version", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    if not root.is_dir():
        print(f"make_sbom: not a directory: {root}", file=sys.stderr)
        return 2

    sbom = build(root, args.name, args.version)
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys so two runs over identical input differ only in the timestamp.
    out.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"make_sbom: {len(sbom['components'])} components -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
