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
import tempfile
import tomllib
from contextlib import contextmanager
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


def confirm_wipe(device: str, hostname: str, username: str, ssh_key_count: int) -> None:
    print()
    print("About to install with:")
    print(f"  device:   {device}  (WILL BE WIPED)")
    print(f"  hostname: {hostname}")
    print(f"  user:     {username}  (sudo, root left locked)")
    print(f"  ssh keys: {ssh_key_count} (password auth will be disabled)" if ssh_key_count
          else "  ssh keys: none (sshd left at its default config)")
    print()
    typed = input(f"Type the device path ({device}) to confirm and continue: ").strip()
    if typed != device:
        sys.exit("Confirmation did not match. Aborting, nothing was touched.")


def nth_partition(device: str, n: int) -> str:
    out = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,PATH,PARTN", device],
        capture_output=True, text=True, check=True,
    ).stdout

    def find(node: dict) -> str | None:
        if node.get("partn") == n:
            return node["path"]
        for child in node.get("children", []):
            if found := find(child):
                return found
        return None

    for node in json.loads(out).get("blockdevices", []):
        if found := find(node):
            return found
    sys.exit(f"Could not find partition {n} on {device}.")


@contextmanager
def mounted_target(device: str, luks_passphrase: str):
    """Open/mount the just-installed root partition for post-install
    touch-ups, independent of whatever mount state archinstall left behind
    at exit (undocumented, so not something to rely on)."""
    root_partition = nth_partition(device, 2)
    mapper_name = "arch_post_install"
    mnt = Path(tempfile.mkdtemp(prefix="arch-post-install-"))
    try:
        opened = subprocess.run(
            ["cryptsetup", "open", root_partition, mapper_name, "--key-file", "-"],
            input=luks_passphrase, text=True,
        )
        root_device = f"/dev/mapper/{mapper_name}" if opened.returncode == 0 else root_partition
        run(["mount", root_device, str(mnt)])
        yield mnt
    finally:
        subprocess.run(["umount", str(mnt)])
        subprocess.run(["cryptsetup", "close", mapper_name])
        mnt.rmdir()


def provision_ssh_access(mnt: Path, username: str, pubkeys: list[str]) -> None:
    """Authorize the collected SSH public keys for `username` on the target,
    and harden sshd to disable password auth."""
    passwd_line = next(
        line for line in Path(mnt, "etc/passwd").read_text().splitlines()
        if line.startswith(f"{username}:")
    )
    uid, gid = (int(x) for x in passwd_line.split(":")[2:4])

    ssh_dir = Path(mnt, "home", username, ".ssh")
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    os.chown(ssh_dir, uid, gid)
    authorized_keys = ssh_dir / "authorized_keys"
    authorized_keys.write_text("\n".join(pubkeys) + "\n")
    authorized_keys.chmod(0o600)
    os.chown(authorized_keys, uid, gid)

    sshd_dropin = Path(mnt, "etc/ssh/sshd_config.d/10-harden.conf")
    sshd_dropin.parent.mkdir(parents=True, exist_ok=True)
    sshd_dropin.write_text(
        "PasswordAuthentication no\n"
        "KbdInteractiveAuthentication no\n"
        "PubkeyAuthentication yes\n"
    )

    run(["arch-chroot", str(mnt), "systemctl", "enable", "sshd.service"])
    print(f"Authorized {len(pubkeys)} SSH key(s) for {username}, disabled SSH password auth.")


def copy_wifi_config(mnt: Path) -> int:
    """Copy the live environment's iwd network profiles (saved by `iwctl
    connect`) to the target, so wifi that's already working here keeps
    working after reboot. archinstall only does this automatically for
    network_config type "iso" - we use "nm_iwd" instead (NetworkManager, for
    a proper GUI applet on the desktop, with iwd as its backend), which
    doesn't carry these over on its own. iwd reads its known-networks from
    this same path regardless of whether it's run standalone or driven by
    NetworkManager, so a plain file copy is enough."""
    live_iwd = Path("/var/lib/iwd")
    psks = list(live_iwd.glob("*.psk")) if live_iwd.exists() else []
    if not psks:
        return 0
    target_iwd = Path(mnt, "var/lib/iwd")
    target_iwd.mkdir(parents=True, exist_ok=True)
    for psk in psks:
        shutil.copy2(psk, target_iwd / psk.name)
    return len(psks)


def profile_has_tag(profile: str, tag: str) -> bool:
    data = tomllib.loads(Path(HERE, "packages.toml").read_text())
    return tag in data.get("profiles", {}).get(profile, [])


def install_claude_code(mnt: Path) -> None:
    """Install Claude Code globally via npm inside the target. Needs a
    working /etc/resolv.conf inside the chroot - a bare post-install chroot
    has nothing running to manage it, unlike a real boot."""
    live_resolv_conf = Path("/etc/resolv.conf")
    if live_resolv_conf.exists():
        shutil.copy(live_resolv_conf, Path(mnt, "etc/resolv.conf"))
    result = subprocess.run(["arch-chroot", str(mnt), "npm", "install", "-g", "@anthropic-ai/claude-code"])
    if result.returncode != 0:
        print("Warning: failed to install Claude Code - install manually later with:")
        print("  npm install -g @anthropic-ai/claude-code")
    else:
        print("Installed Claude Code globally.")


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
    parser.add_argument("--ssh-keys", default=HERE / "ssh_authorized_keys.generated", type=Path)
    parser.add_argument("--profile", default="workstation",
                         help="Profile from packages.toml to resolve the packages list from")
    args = parser.parse_args()

    if shutil.which("archinstall") is None:
        sys.exit("archinstall not found on PATH. Run this from the Arch ISO live environment.")
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        sys.exit("Must run as root (archinstall requires it) - avoids retyping passwords for nothing.")

    template_cmd = [sys.executable, str(HERE / "template_config.py"),
                     "--template", str(args.template), "--output", str(args.config),
                     "--profile", args.profile, "--chained"]
    if args.hostname:
        template_cmd += ["--hostname", args.hostname]
    if args.device:
        template_cmd += ["--device", args.device]
    run(template_cmd)

    run([sys.executable, str(HERE / "check_packages.py"), "--config", str(args.config)])

    generated = json.loads(args.config.read_text())
    device = generated["disk_config"]["device_modifications"][0]["device"]
    hostname = generated.get("hostname", "CHANGEME")

    creds_cmd = [sys.executable, str(HERE / "generate_creds.py"), "--output", str(args.creds)]
    if args.username:
        creds_cmd += ["--username", args.username]
    run(creds_cmd)

    creds_data = json.loads(args.creds.read_text())
    username = creds_data["users"][0]["username"]
    luks_passphrase = creds_data["encryption_password"]

    run([sys.executable, str(HERE / "provision_ssh.py"), "--output", str(args.ssh_keys), "--comment", hostname])
    pubkeys = [line for line in args.ssh_keys.read_text().splitlines() if line.strip()]

    confirm_wipe(device, hostname, username, len(pubkeys))

    print(f"Releasing anything holding {device} busy (old mounts/swap/LUKS mappings)...")
    release_device(device)

    run(["archinstall", "--config", str(args.config), "--creds", str(args.creds)])

    has_wifi = bool(list(Path("/var/lib/iwd").glob("*.psk"))) if Path("/var/lib/iwd").exists() else False
    install_claude = profile_has_tag(args.profile, "dev")
    if pubkeys or has_wifi or install_claude:
        with mounted_target(device, luks_passphrase) as mnt:
            if pubkeys:
                provision_ssh_access(mnt, username, pubkeys)
            if wifi_count := copy_wifi_config(mnt):
                print(f"Copied {wifi_count} wifi network profile(s) - should auto-connect on first boot.")
            if install_claude:
                install_claude_code(mnt)
    args.ssh_keys.unlink(missing_ok=True)

    if args.keep_creds:
        print(f"Kept {args.creds} (--keep-creds passed).")
    else:
        args.creds.unlink(missing_ok=True)
        print(f"Install succeeded, removed {args.creds}.")


if __name__ == "__main__":
    main()
