#!/usr/bin/env python3
"""Chain template_config.py -> generate_creds.py -> archinstall into one
guided run, with a confirmation gate before the destructive disk wipe.

Run this from the Arch ISO live environment on the target machine, as root
(archinstall needs root regardless; checked here early so you don't retype
passwords just to hit a permission error afterwards).

Usage:
    python install.py
    python install.py --hostname lab-03
    python install.py --device /dev/sda --hostname lab-03 --username seba
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def release_device(device: str) -> None:
    """Release anything holding the target device busy - a mounted filesystem,
    active swap, or an open LUKS mapping from a previous install left on the
    disk - so archinstall's own wipefs doesn't fail with 'Device or resource
    busy'. Hit in practice on a machine that already had an encrypted install
    on it from an earlier attempt."""
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,PATH,FSTYPE,MOUNTPOINT", device],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        return

    def release(node: dict) -> None:
        children = node.get("children", [])
        for child in children:
            release(child)
        path = node.get("path")
        if node.get("mountpoint"):
            subprocess.run(["umount", path])
            print(f"  unmounted {path}")
        elif node.get("fstype") == "swap":
            subprocess.run(["swapoff", path])
            print(f"  swapoff {path}")
        if node.get("fstype") == "crypto_LUKS":
            for child in children:
                name = Path(child["path"]).name
                subprocess.run(["cryptsetup", "close", name])
                print(f"  closed LUKS mapping {name}")

    for node in json.loads(out.stdout).get("blockdevices", []):
        release(node)


def confirm_wipe(device: str, hostname: str, username: str) -> None:
    print()
    print("About to install with:")
    print(f"  device:   {device}  (WILL BE WIPED)")
    print(f"  hostname: {hostname}")
    print(f"  user:     {username}  (sudo, root left locked)")
    print()
    typed = input(f"Type the device path ({device}) to confirm and continue: ").strip()
    if typed != device:
        sys.exit("Confirmation did not match. Aborting, nothing was touched.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--template", default=HERE / "user_configuration.json", type=Path)
    parser.add_argument("--config", default=HERE / "user_configuration.generated.json", type=Path)
    parser.add_argument("--creds", default=HERE / "user_credentials.json", type=Path)
    parser.add_argument("--hostname", default=None)
    parser.add_argument("--device", default=None, help="Skip disk detection, use this device path directly")
    parser.add_argument("--username", default=None, help="Skip the username prompt")
    parser.add_argument("--keep-creds", action="store_true",
                         help="Don't delete user_credentials.json after a successful install")
    args = parser.parse_args()

    if shutil.which("archinstall") is None:
        sys.exit("archinstall not found on PATH. Run this from the Arch ISO live environment.")
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        sys.exit("Must run as root (archinstall requires it) - avoids retyping passwords for nothing.")

    template_cmd = [sys.executable, str(HERE / "template_config.py"),
                     "--template", str(args.template), "--output", str(args.config)]
    if args.hostname:
        template_cmd += ["--hostname", args.hostname]
    if args.device:
        template_cmd += ["--device", args.device]
    run(template_cmd)

    generated = json.loads(args.config.read_text())
    device = generated["disk_config"]["device_modifications"][0]["device"]
    hostname = generated.get("hostname", "CHANGEME")

    creds_cmd = [sys.executable, str(HERE / "generate_creds.py"), "--output", str(args.creds)]
    if args.username:
        creds_cmd += ["--username", args.username]
    run(creds_cmd)

    username = json.loads(args.creds.read_text())["users"][0]["username"]

    confirm_wipe(device, hostname, username)

    print(f"Releasing anything holding {device} busy (old mounts/swap/LUKS mappings)...")
    release_device(device)

    run(["archinstall", "--config", str(args.config), "--creds", str(args.creds)])

    if args.keep_creds:
        print(f"Kept {args.creds} (--keep-creds passed).")
    else:
        args.creds.unlink(missing_ok=True)
        print(f"Install succeeded, removed {args.creds}.")


if __name__ == "__main__":
    main()
