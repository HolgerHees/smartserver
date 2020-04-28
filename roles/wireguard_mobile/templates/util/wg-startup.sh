#!/bin/sh
cd /etc/wireguard

VPN_NETWORK="{{vpn_mobile_network}}"
SERVER_ADDRESS="${VPN_NETWORK%.*}.10"

{% for username in vault_usernames %}
CLIENT_{{username}}_ADDRESS="${VPN_NETWORK%.*}.{{loop.index+10}}"
{% endfor %}
    
if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

{% for username in vault_usernames %}
if [ ! -f ./keys/client_{{username}}_privatekey ] || [ ! -f ./keys/client_{{username}}_publickey ]
then
    wg genkey | tee ./keys/client_{{username}}_privatekey | wg pubkey > ./keys/client_{{username}}_publickey
fi
{% endfor %}
    
if [ ! -f wg0.conf ]
then
    echo "[Interface]" > wg0.conf
    echo -n "PrivateKey = " >> wg0.conf
    cat ./keys/server_privatekey >> wg0.conf
    echo -n "Address = " >> wg0.conf
    echo -n $SERVER_ADDRESS >> wg0.conf
    echo "/24" >> wg0.conf
    echo "ListenPort = {{vault_wireguard_mobile_internal_port}}" >> wg0.conf
    echo "SaveConfig = true" >> wg0.conf

{% for username in vault_usernames %}
    echo "[Peer]" >> wg0.conf
    echo -n "AllowedIPs = " >> wg0.conf
    echo -n $CLIENT_{{username}}_ADDRESS >> wg0.conf
    echo "/32" >> wg0.conf
    echo -n "PublicKey = " >> wg0.conf
    cat ./keys/client_{{username}}_publickey >> wg0.conf

{% endfor %}

    chmod 600 wg0.conf
fi

{% for username in vault_usernames %}
if [ ! -f ./clients/wg_{{username}}.conf ]
then
    echo "[Interface]" > ./clients/wg_{{username}}.conf
    echo -n "Address = " >> ./clients/wg_{{username}}.conf
    echo -n $CLIENT_{{username}}_ADDRESS >> ./clients/wg_{{username}}.conf
    echo "/24" >> ./clients/wg_{{username}}.conf
    echo -n "PrivateKey = " >> ./clients/wg_{{username}}.conf
    cat ./keys/client_{{username}}_privatekey >> ./clients/wg_{{username}}.conf
    echo "ListenPort = {{vault_wireguard_mobile_public_port}}" >> ./clients/wg_{{username}}.conf
    echo "DNS = {{server_ip}}" >> ./clients/wg_{{username}}.conf
    
    echo "[Peer]" >> ./clients/wg_{{username}}.conf
    echo -n "PublicKey = " >> ./clients/wg_{{username}}.conf
    cat ./keys/server_publickey >> ./clients/wg_{{username}}.conf
    echo "AllowedIPs = {{server_network}}/24" >> ./clients/wg_{{username}}.conf
    echo "Endpoint = {{public_server_domain}}:{{vault_wireguard_mobile_public_port}}" >> ./clients/wg_{{username}}.conf
    #echo "PersistentKeepalive = 25" >> ./clients/wg_{{username}}.conf

    chmod 600 ./clients/wg_{{username}}.conf
fi
{% endfor %}

ip link del dev wg0

wg-quick up /etc/wireguard/wg0.conf

#iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
#iptables -A FORWARD -i wg0 -j ACCEPT

trap "echo TRAPed signal" HUP INT QUIT TERM

tail -f /dev/null
