#!/bin/sh
cd /etc/wireguard/config

if [ ! -f wg0.conf ]
then
    SERVER_ADDRESS="10.200.0.10"
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey

    echo "[Interface]" > wg0.conf
    echo -n "PrivateKey = " >> wg0.conf
    cat ./keys/server_privatekey >> wg0.conf
    echo -n "Address = " >> wg0.conf
    echo -n $SERVER_ADDRESS >> wg0.conf
    echo "/24" >> wg0.conf
    echo -n "ListenPort = " >> wg0.conf
    echo $EXPOSED_PORT >> wg0.conf
    echo "SaveConfig = true" >> wg0.conf
    
    chmod 700 wg0.conf
fi

if [ -f wg0.conf ]
then
    wg-quick up /etc/wireguard/config/wg0.conf
    
    trap "echo TRAPed signal" HUP INT QUIT TERM

    tail -f /dev/null
fi
