#!/bin/bash

set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo "Must be run as root"
  exit 1
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}"

sudo apt update
sudo apt install -y net-tools
sudo apt install -y python3
sudo apt install -y python3-pip
sudo apt install -y python3-venv
sudo apt install -y hostapd
sudo apt install -y dnsmasq

python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

sudo systemctl enable dnsmasq
sudo systemctl enable hostapd
sudo rm -r icepi.db
echo '{"password": "T05h1th"}' > SECRETS
python3 scripts/usbGadget.py