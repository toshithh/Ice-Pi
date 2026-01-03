echo "[+] Updating"
sudo apt-get update > /dev/null
echo "[+] Resolving Dependencies"
sudo apt-get install -y net-tools openvpn > /dev/null
sudo apt-get install -y python3 python3-pip python3-venv > /dev/null
sudo apt-get install -y hostapd dnsmasq >/dev/null
sudo apt-get -y install tor >/dev/null
echo "[Done]"
