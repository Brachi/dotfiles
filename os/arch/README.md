# Arch install config

`user_configuration.json` targets archinstall **4.4**'s current config schema. It is not
fully machine-agnostic: archinstall's config format has no device auto-detection or
relative/remainder partition sizing (confirmed against `archinstall/lib/args.py` and
`archinstall/lib/models/device.py` on `master`), so two values (device path, root
partition size) need to be filled in per machine. `template_config.py` does that
automatically — see below. Everything else (packages, locale, encryption, bootloader,
desktop) is shared and does not need editing.

## Before installing on a new machine

Boot the target machine from the Arch ISO, then run `template_config.py` — it detects
the disk via `lsblk`, computes the root partition size, and writes a filled-in copy
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

## Running

```sh
archinstall --config user_configuration.generated.json
```

No passwords are stored in this file (LUKS passphrase, root/user password). archinstall
will prompt for those interactively; everything else runs unattended (`silent: true`).

## Notes

- `packages.txt` is a separate, independently-maintained list — not consumed by
  `user_configuration.json` or archinstall directly.
- `vulkan-intel` in `packages` assumes an Intel iGPU; swap for `vulkan-radeon` (AMD) or
  the Nvidia driver package if installing on different hardware.
