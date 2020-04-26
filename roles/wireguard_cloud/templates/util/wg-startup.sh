#!/bin/sh
cd /etc/wireguard

VPN_NETWORK="{{mobile_vpn_network}}"
SERVER_ADDRESS="${VPN_NETWORK%.*}.10"

if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

if [ ! -f wg0.conf ]
then
    echo "[Interface]" > wg0.conf
    echo -n "PrivateKey = " >> wg0.conf
    cat ./keys/server_privatekey >> wg0.conf
    echo -n "Address = " >> wg0.conf
    echo -n $SERVER_ADDRESS >> wg0.conf
    echo "/24" >> wg0.conf
    echo "ListenPort = {{exposed_port}}" >> wg0.conf
    echo "SaveConfig = true" >> wg0.conf

    chmod 600 wg0.conf
fi

wg-quick up /etc/wireguard/wg0.conf

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i wg0 -j ACCEPT

trap "echo TRAPed signal" HUP INT QUIT TERM

tail -f /dev/null
