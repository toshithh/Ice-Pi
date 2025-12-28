#!/bin/bash

AP_IF=$2
WAN_IF=$3
TOR_UID=$(id -u debian-tor)


if [[ $1 == "forward" ]];then
    sudo iptables -A OUTPUT -m owner --uid-owner $TOR_UID -j ACCEPT                           
    sudo iptables -A OUTPUT -o lo -j ACCEPT 
    sudo iptables -t nat -A PREROUTING -i $AP_IF -p udp --dport 53 -j REDIRECT --to-ports 5353
    sudo iptables -t nat -A PREROUTING -i $AP_IF -p tcp --dport 53 -j REDIRECT --to-ports 5353
    sudo iptables -t nat -A PREROUTING -i $AP_IF -p tcp --syn -j REDIRECT --to-ports 9040
    sudo iptables -A FORWARD -i $AP_IF -o $WAN_IF -j DROP                                
    sudo iptables -A FORWARD -i $WAN_IF -o $AP_IF -m state --state ESTABLISHED,RELATED -j ACCEPT
    sudo iptables -t nat -A POSTROUTING -o $WAN_IF -j MASQUERADE
    echo "[+] Routing traffic through Tor!"
elif [[ $1 == "stop" ]];then
    sudo iptables -D OUTPUT -m owner --uid-owner "$TOR_UID" -j ACCEPT 2>/dev/null || true
    sudo iptables -D OUTPUT -o lo -j ACCEPT 2>/dev/null || true
    sudo iptables -t nat -D PREROUTING -i "$AP_IF" -p udp --dport 53 -j REDIRECT --to-ports 5353 2>/dev/null || true
    sudo iptables -t nat -D PREROUTING -i "$AP_IF" -p tcp --dport 53 -j REDIRECT --to-ports 5353 2>/dev/null || true
    sudo iptables -t nat -D PREROUTING -i "$AP_IF" -p tcp --syn -j REDIRECT --to-ports 9040 2>/dev/null || true
    sudo iptables -D FORWARD -i "$AP_IF" -o "$WAN_IF" -j DROP 2>/dev/null || true
    sudo iptables -D FORWARD -i "$WAN_IF" -o "$AP_IF" -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
    sudo iptables -t nat -D POSTROUTING -o "$WAN_IF" -j MASQUERADE 2>/dev/null || true
    echo "[-] Not routing through Tor anymore!"
fi

