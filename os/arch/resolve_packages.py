#!/usr/bin/env python3
"""Resolve packages.toml's tags into a flat, deduplicated package list.

Usage:
    python resolve_packages.py --profile workstation
    python resolve_packages.py --profile homelab-server
    python resolve_packages.py --tags base,dev
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).parent


def resolve(data: dict, tags: list[str]) -> list[str]:
    packages: set[str] = set()
    for tag in tags:
        if tag not in data.get("tags", {}):
            sys.exit(f"Unknown tag: {tag!r} (known: {sorted(data.get('tags', {}))})")
        packages.update(data["tags"][tag]["packages"])
    return sorted(packages)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default=HERE / "packages.toml", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", help="Named combination of tags from [profiles] in packages.toml")
    group.add_argument("--tags", help="Comma-separated tag names, e.g. base,dev")
    args = parser.parse_args()

    data = tomllib.loads(args.file.read_text())

    if args.profile:
        profiles = data.get("profiles", {})
        if args.profile not in profiles:
            sys.exit(f"Unknown profile: {args.profile!r} (known: {sorted(profiles)})")
        tags = profiles[args.profile]
    else:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    for package in resolve(data, tags):
        print(package)


if __name__ == "__main__":
    main()
