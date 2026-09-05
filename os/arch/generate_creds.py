#!/usr/bin/env python3
"""Generate user_credentials.json interactively: a LUKS passphrase and one
sudo-enabled user. Root is left locked (no root_enc_password in the output)
— administer via the sudo user instead. This is a deliberate default, not
an oversight: omitting root_enc_password from the creds file is how
archinstall leaves root's shadow entry locked ('*') while still creating a
working login (confirmed against archinstall/lib/args.py on the live ISO).

Without a --creds file at all, `archinstall --config ... --silent` does NOT
prompt for credentials — it silently proceeds and installs a system with a
locked root and no user account, i.e. nothing can log in. A creds file is
mandatory for a usable install, not optional.

The output file contains password hashes and a plaintext LUKS passphrase
(archinstall's own creds schema requires the LUKS password in plaintext,
see examples/creds-sample.json) — it must never be committed. It only needs
to exist on the live ISO's ephemeral filesystem for the duration of the
install.

Usage:
    python generate_creds.py
    archinstall --config user_configuration.generated.json --creds user_credentials.json
"""

from __future__ import annotations

import argparse
import getpass
import json
import subprocess
import sys
from pathlib import Path


def prompt_password(label: str) -> str:
    while True:
        first = getpass.getpass(f"{label}: ")
        if not first:
            print("Password cannot be empty.", file=sys.stderr)
            continue
        second = getpass.getpass(f"{label} (confirm): ")
        if first != second:
            print("Passwords did not match, try again.", file=sys.stderr)
            continue
        return first


def hash_password(password: str) -> str:
    return subprocess.run(
        ["openssl", "passwd", "-6", "-stdin"],
        input=password, capture_output=True, text=True, check=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--username", default=None, help="Skip the username prompt")
    parser.add_argument("--output", default=Path(__file__).with_name("user_credentials.json"), type=Path)
    args = parser.parse_args()

    username = args.username or input("Username: ").strip()
    if not username:
        sys.exit("Username cannot be empty.")

    user_password = prompt_password(f"Password for {username}")
    luks_password = prompt_password("LUKS encryption passphrase")

    creds = {
        "encryption_password": luks_password,
        "users": [
            {
                "sudo": True,
                "username": username,
                "enc_password": hash_password(user_password),
            }
        ],
    }

    args.output.write_text(json.dumps(creds, indent=4) + "\n")
    try:
        args.output.chmod(0o600)
    except OSError:
        pass
    print(f"Wrote {args.output}")
    print(f"  root: locked (no password) — administer via '{username}' + sudo")


if __name__ == "__main__":
    main()
