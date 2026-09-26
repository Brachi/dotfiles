#!/usr/bin/bash
# Home printer/scanner: Brother MFC-J1010DW, driverless both ways - AirPrint
# (IPP Everywhere) for printing, eSCL for scanning - so no vendor drivers or
# AUR packages. Needs cups and sane-airscan (desktop tag in packages.toml).
#
# Addresses the printer by the hostname it registers with the router, not an
# IP, so a new DHCP lease doesn't break it. The scanner is listed explicitly
# instead of discovered, so avahi-daemon doesn't need to run.
#
# Run once per machine that should use it; safe to re-run.
set -euo pipefail

HOST=BRW3C0AF349AF8B.lan
QUEUE=MFC-J1010DW-airprint

sudo systemctl enable --now cups.socket

sudo lpadmin -p "$QUEUE" -D "Brother MFC-J1010DW" -E -v "ipp://$HOST/ipp/print" -m everywhere
sudo lpadmin -d "$QUEUE"

sudo install -d /etc/sane.d/airscan.d
printf '[devices]\n"Brother MFC-J1010DW" = http://%s/eSCL, eSCL\n' "$HOST" \
    | sudo tee /etc/sane.d/airscan.d/brother.conf > /dev/null

echo "Printer '$QUEUE' set as default; scanner configured for sane-airscan."
