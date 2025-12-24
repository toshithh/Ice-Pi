#!/bin/bash

sudo apt update
sudo apt install -y net-tools
sudo apt install -y python3 
sudo apt install -y python3-pip
sudo apt install -y python3-venv
sudo apt install -y hostapd
sudo apt install -y dnsmasq 
sudo apt install -y dhcpcd 

python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt