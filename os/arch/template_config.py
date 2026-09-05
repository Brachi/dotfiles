#!/usr/bin/env python3
"""Fill in the hardware-specific placeholders in user_configuration.json.

archinstall's config format has no device auto-detection or relative/remainder
partition sizing (confirmed against archinstall/lib/args.py and
archinstall/lib/models/device.py — no wildcard device, no Percent unit, and
its --plugin hooks only fire after disk_config has already been resolved).
So this script does the one thing archinstall itself can't: pick the target
disk and compute a root partition size, before archinstall ever runs.

Run this from the Arch ISO live environment on the target machine (network
required, same as archinstall itself), then hand the generated file to
archinstall.

Usage:
    python template_config.py
    python template_config.py --hostname lab-03
    python template_config.py --device /dev/sda --hostname lab-03
    archinstall --config user_configuration.generated.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ESP_START_MIB = 1
ESP_SIZE_MIB = 1024
ROOT_START_MIB = ESP_START_MIB + ESP_SIZE_MIB
END_RESERVE_MIB = 2  # headroom for the GPT backup header at the end of the disk


def list_disks() -> list[dict]:
    """Candidate target disks, excluding the live boot medium by transport
    (TRAN == "usb") so it can't be wiped out from under itself.

    Two earlier approaches both failed on real hardware: matching what's
    mounted on /run/archiso/bootmnt (that path can resolve through a
    loop/overlay mount rather than the raw partition, so it silently excluded
    nothing), and excluding any disk with a mounted partition at all (this
    archiso mounts the boot stick only long enough to loop-mount its squashfs,
    then leaves the stick itself unmounted - so that check also excluded
    nothing there, and worse, wrongly excluded the *target* disk too whenever
    an interrupted previous install attempt left it with a stale mount).
    Transport doesn't depend on mount state at all, so it doesn't have either
    problem.
    """
    out = subprocess.run(
        ["lsblk", "-J", "-b", "-o", "NAME,PATH,SIZE,TYPE,RO,TRAN"],
        check=True, capture_output=True, text=True,
    ).stdout
    disks = []
    for dev in json.loads(out).get("blockdevices", []):
        if dev.get("type") != "disk" or dev.get("ro"):
            continue
        # lsblk reports zram/loop/etc. as type "disk" too; only keep devices
        # backed by real hardware (they have a /sys/block/<name>/device link).
        if not Path("/sys/block", dev["name"], "device").exists():
            continue
        if dev.get("tran") == "usb":
            continue
        disks.append({"path": dev["path"], "size": int(dev["size"])})
    return disks


def pick_disk(disks: list[dict]) -> dict:
    if not disks:
        sys.exit("No usable disks found. Aborting.")
    if len(disks) == 1:
        return disks[0]
    print("Multiple disks found:")
    for i, d in enumerate(disks):
        print(f"  [{i}] {d['path']}  ({d['size'] / 1024**3:.1f} GiB)")
    choice = input("Select target disk index: ").strip()
    try:
        return disks[int(choice)]
    except (ValueError, IndexError):
        sys.exit("Invalid selection. Aborting.")


def disk_size(device: str) -> int:
    out = subprocess.run(
        ["lsblk", "-b", "-n", "-d", "-o", "SIZE", device],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return int(out.splitlines()[0])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--template", default=Path(__file__).with_name("user_configuration.json"), type=Path)
    parser.add_argument("--output", default=Path(__file__).with_name("user_configuration.generated.json"), type=Path)
    parser.add_argument("--hostname", default=None)
    parser.add_argument("--device", default=None, help="Skip disk detection, use this device path directly")
    parser.add_argument("--profile", default="workstation",
                         help="Profile from packages.toml to resolve the packages list from")
    parser.add_argument("--chained", action="store_true",
                         help="Suppress the standalone 'run archinstall yourself next' hint - "
                              "pass this when called from install.py, which runs archinstall itself")
    args = parser.parse_args()

    config = json.loads(args.template.read_text())

    resolved = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("resolve_packages.py")), "--profile", args.profile],
        check=True, capture_output=True, text=True,
    ).stdout
    config["packages"] = resolved.splitlines()

    if args.device:
        target = {"path": args.device, "size": disk_size(args.device)}
    else:
        target = pick_disk(list_disks())

    root_size_mib = (target["size"] // (1024 * 1024)) - ROOT_START_MIB - END_RESERVE_MIB
    if root_size_mib <= 0:
        sys.exit(f"Disk {target['path']} is too small for this layout.")

    dev_mod = config["disk_config"]["device_modifications"][0]
    dev_mod["device"] = target["path"]
    root_partition = dev_mod["partitions"][1]
    root_partition["size"] = {
        "sector_size": {"unit": "B", "value": 512},
        "unit": "MiB",
        "value": root_size_mib,
    }

    if args.hostname:
        config["hostname"] = args.hostname
    elif config.get("hostname") == "CHANGEME":
        print("Warning: hostname left as CHANGEME (pass --hostname to set it).", file=sys.stderr)

    args.output.write_text(json.dumps(config, indent=4) + "\n")
    print(f"Wrote {args.output}")
    print(f"  device: {target['path']}")
    print(f"  root partition: {root_size_mib} MiB ({root_size_mib / 1024:.1f} GiB)")
    if not args.chained:
        print(f"Review it, then run: archinstall --config {args.output}")


if __name__ == "__main__":
    main()
