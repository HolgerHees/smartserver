#!/bin/sh
cd /etc/wireguard

VPN_NETWORK="{{vpn_mobile_network}}"
SERVER_ADDRESS="${VPN_NETWORK%.*}.10"

{% for name in vpn_gates %}
CLIENT_{{name}}_ADDRESS="${VPN_NETWORK%.*}.{{loop.index+10}}"
{% endfor %}
    
initDeviceConfig()
{
    echo "[Interface]" > wg0.conf
    echo -n "PrivateKey = " >> wg0.conf
    cat ./keys/server_privatekey >> wg0.conf
    echo -n "Address = " >> wg0.conf
    echo -n $SERVER_ADDRESS >> wg0.conf
    echo "/24" >> wg0.conf
    echo "ListenPort = {{vault_wireguard_mobile_internal_port}}" >> wg0.conf
    echo "SaveConfig = true" >> wg0.conf

{% for name in vpn_gates %}
    echo "[Peer]" >> wg0.conf
    echo -n "AllowedIPs = " >> wg0.conf
    echo -n $CLIENT_{{name}}_ADDRESS >> wg0.conf
    echo "/32" >> wg0.conf
    echo -n "PublicKey = " >> wg0.conf
    cat ./keys/client_{{name}}_publickey >> wg0.conf

{% endfor %}
    chmod 600 wg0.conf
}

initClientConfigs()
{
    echo "[Interface]" > $1
    echo -n "Address = " >> $1
    echo -n $3 >> $1
    echo "/24" >> $1
    echo -n "PrivateKey = " >> $1
    cat $2 >> $1
    echo "ListenPort = {{vault_wireguard_mobile_public_port}}" >> $1
    echo "DNS = {{server_ip}}" >> $1
    
    echo "[Peer]" >> $1
    echo -n "PublicKey = " >> $1
    cat ./keys/server_publickey >> $1
    echo "AllowedIPs = {{server_network}}/24" >> $1
    echo "Endpoint = {{public_server_domain}}:{{vault_wireguard_mobile_public_port}}" >> $1
    #echo "PersistentKeepalive = 25" >> $1

    chmod 600 $1
}

stop()
{
    echo "SIGTERM caught, shutting down wireguard interfaces..."

    wg-quick down wg0
  
    echo "done"
    exit
}

start()
{
    ip link del dev wg0 > /dev/null 2>&1

    wg-quick up ./wg0.conf
}

if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

{% for name in vpn_gates %}
if [ ! -f ./keys/client_{{name}}_privatekey ] || [ ! -f ./keys/client_{{name}}_publickey ]
then
    wg genkey | tee ./keys/client_{{name}}_privatekey | wg pubkey > ./keys/client_{{name}}_publickey
fi
{% endfor %}
    
if [ ! -f wg0.conf ]
then
    initDeviceConfig
fi

{% for name in vpn_gates %}
if [ ! -f ./clients/wg_{{name}}.conf ]
then
    initClientConfigs './clients/wg_{{name}}.conf' './keys/client_{{name}}_privatekey' $CLIENT_{{name}}_ADDRESS
fi
{% endfor %}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1
