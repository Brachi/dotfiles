#!/usr/bin/env python3
"""Verify every package actually resolves via pacman - catches typos,
renamed packages, and AUR-only packages that would otherwise only surface
as a pacstrap failure partway through archinstall, after the disk is
already wiped.

Usage:
    python check_packages.py --toml packages.toml
    python check_packages.py --config user_configuration.generated.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path


def bad_packages(names: list[str]) -> list[str]:
    bad = []
    for name in names:
        result = subprocess.run(["pacman", "-Si", name], capture_output=True)
        if result.returncode != 0:
            bad.append(name)
    return bad


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path, help="Check the 'packages' array of a generated archinstall config")
    group.add_argument("--toml", type=Path, help="Check every package across all tags in packages.toml")
    args = parser.parse_args()

    if args.config:
        names = json.loads(args.config.read_text())["packages"]
    else:
        data = tomllib.loads(args.toml.read_text())
        names = sorted({p for tag in data["tags"].values() for p in tag["packages"]})

    if bad := bad_packages(names):
        sys.exit(f"Not found via pacman (typo, renamed, or AUR-only - not installable by archinstall): "
                  f"{', '.join(bad)}")
    print(f"All {len(names)} packages resolve via pacman.")


if __name__ == "__main__":
    main()
