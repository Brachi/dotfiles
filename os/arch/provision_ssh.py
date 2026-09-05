#!/usr/bin/env python3
"""Generate resident (discoverable) FIDO2 SSH keys directly on hardware
security keys (YubiKeys etc.) and collect their public keys into a plain
authorized_keys-format file.

Each key is generated ON the device itself via `ssh-keygen -O resident` -
the private key material never leaves the hardware; ssh-keygen just writes a
small local "handle" stub (discarded here) plus the public key, which is all
that's needed to authorize logins. The same resident credential can later be
retrieved from the hardware again elsewhere via `ssh-keygen -K`.

Requires libfido2 and an ssh-keygen build with security-key support - both
present in a stock Arch install; if the live ISO is missing libfido2, this
will say so rather than failing with a confusing ssh-keygen error.

Usage:
    python provision_ssh.py
    python provision_ssh.py --output authorized_keys --comment lab-03
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def check_fido2_support() -> None:
    supported = subprocess.run(["ssh", "-Q", "key"], capture_output=True, text=True).stdout
    if "sk-ssh-ed25519@openssh.com" not in supported:
        sys.exit(
            "This ssh-keygen has no FIDO2/security-key support.\n"
            "On the Arch ISO, try: pacman -Sy libfido2 openssh"
        )


def generate_one(comment: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        keyfile = Path(tmp) / "key"
        result = subprocess.run([
            "ssh-keygen", "-t", "ed25519-sk", "-O", "resident", "-O", "verify-required",
            "-N", "", "-C", comment, "-f", str(keyfile),
        ])
        if result.returncode != 0:
            sys.exit(
                "ssh-keygen failed - key not inserted, PIN wrong/not set, "
                "or touch not confirmed in time."
            )
        return keyfile.with_suffix(".pub").read_text().strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--output", default=Path(__file__).with_name("ssh_authorized_keys.generated"), type=Path)
    parser.add_argument("--comment", default="arch-lab", help="Comment embedded in each generated key")
    args = parser.parse_args()

    choice = input("Add FIDO2 security key(s) for passwordless SSH login? [Y/n]: ").strip().lower()
    if choice == "n":
        args.output.write_text("")
        print(f"Skipped - wrote empty {args.output}.")
        return

    check_fido2_support()

    keys: list[str] = []
    n = 1
    while True:
        input(f"Insert security key #{n}, then press Enter here (you'll be asked to touch it "
              f"and enter its PIN)...")
        pubkey = generate_one(f"{args.comment}-key{n}")
        keys.append(pubkey)
        print(f"  captured key #{n}")
        n += 1
        if input("Add another key? [y/N]: ").strip().lower() != "y":
            break

    args.output.write_text("\n".join(keys) + "\n")
    print(f"Wrote {len(keys)} key(s) to {args.output}")


if __name__ == "__main__":
    main()
