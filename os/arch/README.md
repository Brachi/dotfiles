# Arch install config

`user_configuration.json` targets archinstall **4.4**'s current config schema. It is not
fully machine-agnostic: archinstall's config format has no device auto-detection or
relative/remainder partition sizing (confirmed against `archinstall/lib/args.py` and
`archinstall/lib/models/device.py` on `master`), so two values (device path, root
partition size) need to be filled in per machine. `template_config.py` does that
automatically — see below. Locale, encryption, and bootloader settings are shared and
don't need editing; packages depend on which `--profile` you pick (see
[Packages and profiles](#packages-and-profiles)).

## Installing on a new machine

Boot the target machine from the Arch ISO, `cd` into this directory, and run:

```sh
python install.py --hostname lab-03 --profile workstation
```

This chains the three steps below (disk templating, credential generation,
`archinstall` itself) into one guided run. It prints the target device, hostname,
and username, then requires you to type the device path back to confirm before the
disk wipe happens — nothing destructive runs until you do. On a successful install
it deletes the generated `user_credentials.json` (pass `--keep-creds` to keep it, e.g.
if you want to rerun `archinstall` without retyping passwords).

The sections below describe what each step does individually — useful for running
them by hand, or re-running just one after a failure (`install.py` always regenerates
both the config and creds files, so after an `archinstall` failure it's often faster to
rerun `archinstall --config ... --creds ...` directly with the files already on disk
than to go through `install.py` again).

### Disk templating

`template_config.py` detects the disk via `lsblk`, computes the root partition size, and writes a filled-in copy
(it never edits `user_configuration.json` itself). No third-party tooling does this
(checked: archinstall's `--plugin` hooks only fire after disk layout is already
resolved, and no community plugin/wrapper exists for it), so it's a small standalone
script scoped to this file's specific two-partition layout.

```sh
python template_config.py --hostname lab-03
```

It auto-picks the disk if only one is present, and excludes the live-USB boot medium
from candidates. If multiple disks are present it lists them and asks which to use.
Pass `--device /dev/sda` to skip detection and specify one directly.

`disk_config.device_modifications[0].wipe` is `true` — the whole target disk will be
wiped. Double check the printed device path before running archinstall.

To edit by hand instead, replace the two `CHANGEME` values in `user_configuration.json`:
`disk_config.device_modifications[0].device`, and partition `[1]`'s `size.value`
(`(disk size in GiB) - 2`, leaving ~1 GiB for the ESP and a small alignment gap).

### Packages and profiles

`packages.toml` is the single source of truth for packages, tagged by purpose
(`base`, `dev`, `desktop`, `media`, `extra`, `server`). `[profiles]` names which tags to
combine — currently `workstation` (everything, full KDE desktop) and `homelab-server`
(`base` + `dev` + `server`, no desktop/GUI packages at all). `template_config.py` always
overwrites `user_configuration.json`'s `packages` array with the resolved list, so that
field in the template itself is just a placeholder — edit `packages.toml` instead.

```sh
python resolve_packages.py --profile homelab-server   # preview the flat list
python install.py --hostname lab-04 --profile homelab-server
```

Add a package once, under whichever tag(s) fit, rather than editing a profile's list
directly. `--tags base,dev` also works in place of `--profile` for an ad hoc combination.

If the resolved profile includes the `dev` tag, `install.py` also installs Claude Code
globally (`npm install -g @anthropic-ai/claude-code`) inside the target as part of the
same post-install chroot pass used for SSH/wifi — a `resolv.conf` copy from the live
environment is needed first since nothing's running yet inside a bare chroot to manage
DNS. A failure here only warns (with the manual command to run later) rather than
failing the whole install, since it's a nice-to-have, not install-critical.

### Credentials

`user_configuration.json` has `"silent": true`, which disables *all* prompts —
including authentication. **Without a `--creds` file, archinstall does not fall back to
asking interactively: it silently installs a system with root locked (shadow entry `*`)
and no user account, i.e. nothing can log in.** This was verified directly (installed,
then inspected `/etc/shadow` and `/etc/passwd` on the target). A creds file is mandatory,
not optional.

Generate one with `generate_creds.py` (same live-ISO session as `template_config.py`):

```sh
python generate_creds.py
```

It prompts for a username, a password for that user, and the LUKS passphrase, then
writes `user_credentials.json` — password-hashed, gitignored, never committed. Root is
deliberately left locked (no `root_enc_password`); administer via the sudo user instead.
Pass `--username` to skip the username prompt.

### SSH access (optional)

`install.py` also runs `provision_ssh.py`, which offers to generate resident FIDO2 SSH
keys directly on hardware security keys (YubiKeys etc.) via `ssh-keygen -O resident` —
the private key never leaves the device. Decline the prompt for a plain install with no
SSH keys configured (sshd is left at its default config in that case).

If you add at least one key, after `archinstall` finishes `install.py` mounts the new
root filesystem itself (independent of whatever state `archinstall` left it in),
authorizes the collected keys for the sudo user, drops
`/etc/ssh/sshd_config.d/10-harden.conf` (`PasswordAuthentication no`), and enables
`sshd.service`. Run `python provision_ssh.py` standalone to test the hardware step
without a full install; it needs `libfido2` and a security-key-capable `ssh-keygen`
(check with `ssh -Q key | grep sk`) — install with `pacman -Sy libfido2` on the live ISO
if missing.

### Wifi (carried over automatically)

`network_config.type` is `"nm_iwd"` — NetworkManager (so the desktop gets a proper
network applet via `network-manager-applet`) using `iwd` as its wifi backend. If you
connected to wifi on the live ISO with `iwctl` before running this, `install.py` copies
that connection's saved profile from `/var/lib/iwd/` to the target after `archinstall`
finishes, so it's already connected on first boot — no need to reconnect manually.
(archinstall has a built-in `"iso"` network type that does this same copy automatically,
but it skips NetworkManager entirely; since we want the GUI applet, this is done as a
small manual step instead, in the same mount pass as the SSH provisioning above.)

### Console font

`locale_config.console_font` is `"ter-132n"` (large Terminus), not archinstall's default
`default8x16` — at a high output resolution (e.g. a 4K-capable GPU driving a plain text
console), the default font is tiny to the point of being unreadable, noticed while
watching a mini PC's console over an HDMI capture card. archinstall auto-installs
`terminus-font` itself whenever the font name starts with `ter-`, so no package list
changes were needed. This only affects the *installed* system's console (`/etc/vconsole.conf`)
— the live ISO's own shell still uses its own default font; bump that separately and
temporarily with `pacman -Sy terminus-font && setfont ter-132n` if needed.

### Running archinstall directly

```sh
archinstall --config user_configuration.generated.json --creds user_credentials.json
```

## Notes

- `vulkan-intel` in `packages.toml`'s `desktop` tag assumes an Intel iGPU; swap for
  `vulkan-radeon` (AMD) or the Nvidia driver package if installing on different hardware.
