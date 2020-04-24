#!/bin/sh
cd /etc/wireguard/config

if [ ! -f wg0.conf ]
then
    mkdir keys
    mkdir clients

    SERVER_ADDRESS="${VPN_NETWORK%.*}.10"
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey

{% for username in vault_usernames %}
    wg genkey | tee ./keys/client_{{username}}_privatekey | wg pubkey > ./keys/client_{{username}}_publickey
    CLIENT_{{username}}_ADDRESS="${VPN_NETWORK%.*}.{{loop.index+10}}"

{% endfor %}
    
    echo "[Interface]" > wg0.conf
    echo -n "PrivateKey = " >> wg0.conf
    cat ./keys/server_privatekey >> wg0.conf
    echo -n "Address = " >> wg0.conf
    echo -n $SERVER_ADDRESS >> wg0.conf
    echo "/24" >> wg0.conf
    echo "ListenPort = 51820" >> wg0.conf
    echo "SaveConfig = true" >> wg0.conf
    
{% for username in vault_usernames %}
    echo "[Peer]" >> wg0.conf
    echo -n "AllowedIPs = " >> wg0.conf
    echo -n $CLIENT_{{username}}_ADDRESS >> wg0.conf
    echo "/32" >> wg0.conf
    echo -n "PublicKey = " >> wg0.conf
    cat ./keys/client_{{username}}_publickey >> wg0.conf

{% endfor %}

    chmod 700 wg0.conf

{% for username in vault_usernames %}
    echo "[Interface]" > ./clients/wg_{{username}}.conf
    echo -n "Address = " >> ./clients/wg_{{username}}.conf
    echo -n $CLIENT_{{username}}_ADDRESS >> ./clients/wg_{{username}}.conf
    echo "/24" >> ./clients/wg_{{username}}.conf
    echo -n "PrivateKey = " >> ./clients/wg_{{username}}.conf
    cat ./keys/client_{{username}}_privatekey >> ./clients/wg_{{username}}.conf
    echo -n "ListenPort = " >> ./clients/wg_{{username}}.conf
    echo $PORT >> ./clients/wg_{{username}}.conf
    echo -n "DNS = " >> ./clients/wg_{{username}}.conf
    echo $DNS_SERVER >> ./clients/wg_{{username}}.conf
    
    echo "[Peer]" >> ./clients/wg_{{username}}.conf
    echo -n "PublicKey = " >> ./clients/wg_{{username}}.conf
    cat ./keys/server_publickey >> ./clients/wg_{{username}}.conf
    echo -n "AllowedIPs = " >> ./clients/wg_{{username}}.conf
    echo -n $SERVER_NETWORK >> ./clients/wg_{{username}}.conf
    echo "/24" >> ./clients/wg_{{username}}.conf
    echo -n "Endpoint = " >> ./clients/wg_{{username}}.conf
    echo -n $ENDPOINT >> ./clients/wg_{{username}}.conf
    echo -n ":" >> ./clients/wg_{{username}}.conf
    echo $PORT >> ./clients/wg_{{username}}.conf
    #echo "PersistentKeepalive = 25" >> ./clients/wg_{{username}}.conf

    chmod 700 ./clients/wg_{{username}}.conf
    
{% endfor %}
fi

if [ -f wg0.conf ]
then
    wg-quick up /etc/wireguard/config/wg0.conf
    
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    iptables -A FORWARD -i wg0 -j ACCEPT
    
    trap "echo TRAPed signal" HUP INT QUIT TERM

    tail -f /dev/null
fi
