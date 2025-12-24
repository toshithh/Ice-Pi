#!/bin/bash

if [[ $1 == "forward" ]]; then
    sudo sysctl -w net.ipv4.ip_forward=1
    sudo iptables -t nat -A POSTROUTING -o $3 -j MASQUERADE
    sudo iptables -A FORWARD -i $3 -o $2 -m state --state RELATED,ESTABLISHED -j ACCEPT
    sudo iptables -A FORWARD -i $2 -o $3 -j ACCEPT
elif [[ $1 == "stop" ]]; then
    sudo sysctl -w net.ipv4.ip_forward=0
    sudo iptables --flush
fi