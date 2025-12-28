#!/bin/bash

set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo "Must be run as root"
  exit 1
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

echo "[+] Updating"
sudo apt-get update > /dev/null
echo "[+] Resolving Dependencies"
sudo apt-get install -y net-tools openvpn > /dev/null
sudo apt-get install -y python3 python3-pip python3-venv > /dev/null
sudo apt-get install -y hostapd dnsmasq >/dev/null

echo "[Done]"

echo ""
echo "[+] Writing files"
sudo mkdir -p /var/local/IcePi
sudo cp -r config/dnsmasq.conf /etc/dnsmasq.conf
sudo cp -r config/hostapd.conf /etc/hostapd/hostapd.conf
sudo cp -r config/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf
sudo cp -r config/usb-gadget-init.sh /usr/local/sbin/usb-gadget-init.sh
sudo chmod +x /usr/local/sbin/usb-gadget-init.sh
sudo cp -r service/* /etc/systemd/system
echo '{"password": "T05h1th"}' > SECRETS
sudo chmod +x scripts/ipForward.sh
sudo cp -r ./* /var/local/IcePi
echo "[Done]"

cd /var/local/IcePi

echo ""
echo "[+] Setting up virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt >/dev/null
echo "...Done"

echo "[+] Enabling Services"
sudo systemctl unmask hostapd
sudo systemctl enable --now ap-interface.service
sudo systemctl enable --now ice-pi.service
sudo systemctl enable --now dnsmasq
sudo systemctl enable --now hostapd
sudo systemctl enable --now usb-gadget.service

echo "[+] Setting up interfaces"
sudo systemctl restart NetworkManager || sudo systemctl restart networking || sudo systemctl restart dnsmasq || sudo systemctl restart hostapd
echo "[Done]"

echo ""
echo "Ice-Pi set up!"
echo "Please restart your device to load kernel modules!"
