#!/bin/sh
cd /etc/wireguard

if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

PRIVATE_KEY=$(cat ./keys/server_privatekey)

NEW_CONFIG="[Interface]
PrivateKey = ${PRIVATE_KEY}
Address = {{cloud_network.interface.address}}
ListenPort = {{exposed_port}}
SaveConfig = true

{% for peer_network in vault_cloud_vpn_networks %}
{% if peer_network != main_network and vault_cloud_vpn_networks[peer_network].peer.publicKey != '' %}
[Peer]
PublicKey = {{vault_cloud_vpn_networks[peer_network].peer.publicKey}}
AllowedIPs = {{vault_cloud_vpn_networks[peer_network].peer.allowedIPs}}
Endpoint = {{vault_cloud_vpn_networks[peer_network].peer.endpoint}}
{% endif %}
{% endfor %}"

NEW_EXPORTS="{% for peer_network in vault_cloud_vpn_networks %}
{% if peer_network != main_network %}
{{raid_path}}{{data_dir_name}}/local/{{peer_network}} {{vault_cloud_vpn_networks[peer_network].peer.allowedIPs}}(rw,async)
{% endif %}
{% endfor %}"

NEW_MOUNTS="{% for peer_network in vault_cloud_vpn_networks %}
{% if peer_network != main_network %}
{{vault_cloud_vpn_networks[peer_network].peer.nfsServer}}:{{raid_path}}{{data_dir_name}}/local/{{peer_network}} {{raid_path}}{{data_dir_name}}/remote/{{peer_network}} nfs rw 0 0
{% endif %}
{% endfor %}"

#CONFIG="${CONFIG/PRIVATE_KEY/$PRIVATE_KEY}"

OLD_CONFIG=$(cat wg0.conf)

if [ ! -f wg0.conf ] || [ "$OLD_CONFIG" != "$NEW_CONFIG" ]
then
    echo "$NEW_CONFIG" > wg0.conf
    chmod 600 wg0.conf
fi

wg-quick up /etc/wireguard/wg0.conf

#iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
#iptables -A FORWARD -i wg0 -j ACCEPT

trap "echo TRAPed signal" HUP INT QUIT TERM

tail -f /dev/null
