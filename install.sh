#!/bin/bash

set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo "Must be run as root"
  exit 1
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

echo "[+] Updating"
sudo apt update > /dev/null
echo "[+] Resolving Dependencies"
sudo apt install -y net-tools > /dev/null
sudo apt install -y python3 > /dev/null
sudo apt install -y python3-pip >/dev/null
sudo apt install -y python3-venv >/dev/null
sudo apt install -y hostapd >/dev/null
sudo apt install -y dnsmasq >/dev/null

echo "[Done]"

echo ""
echo "[+] Setting up virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt >/dev/null
echo "...Done"

echo ""
echo "[+] Writing files"
sudo mkdir -p /var/local/IcePi
sudo cp -r certs /var/local/IcePi
sudo cp -r config/dnsmasq.conf /etc/dnsmasq.conf
sudo cp -r config/hostapd.conf /etc/hostapd/hostapd.conf
echo '{"password": "T05h1th"}' > SECRETS
chmod +x scripts/ipForward.sh
echo "[Done]"

echo "[+] Enabling Services"
sudo systemctl unmask hostapd
sudo systemctl enable --now dnsmasq
sudo systemctl enable --now hostapd

sudo cp -r config/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf
cd ..
echo "[+] Setting up interfaces"
sudo $(which python3) -m IcePi.scripts.usbGadget
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

sudo systemctl restart NetworkManager || sudo systemctl restart networking || sudo systemctl restart dnsmasq || sudo systemctl restart hostapd
echo "[Done]"

echo ""
echo "Please restart your device to load kernel modules!"