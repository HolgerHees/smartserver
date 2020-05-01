#!/bin/sh
cd /etc/wireguard

initDeviceConfig()
{
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

    OLD_CONFIG=$(cat wg0.conf)

    if [ ! -f wg0.conf ] || [ "$OLD_CONFIG" != "$NEW_CONFIG" ]
    then
        echo "$NEW_CONFIG" > wg0.conf
        chmod 600 wg0.conf
    fi
}

initExports()
{
    NEW_EXPORTS="{% for peer_network in vault_cloud_vpn_networks %}
{% if peer_network != main_network and vault_cloud_vpn_networks[peer_network].peer.publicKey != '' %}
/cloud/local/{{peer_network}} {{vault_cloud_vpn_networks[peer_network].peer.allowedIPs}}(rw,async)
{% endif %}
{% endfor %}"

    OLD_EXPORTS=$(cat /etc/exports)

    if [ ! -f /etc/export ] || [ "$OLD_EXPORTS" != "$NEW_EXPORTS" ]
    then
        echo "$NEW_EXPORTS" > /etc/exports
        chmod 640 /etc/exports
    fi
}

initFstab()
{
{% for peer_network in vault_cloud_vpn_networks %}
{% if peer_network != main_network and vault_cloud_vpn_networks[peer_network].peer.publicKey != '' %}
    if ! grep -q '{{vault_cloud_vpn_networks[peer_network].peer.nfsServer}}' /etc/fstab ; then
        echo '{{vault_cloud_vpn_networks[peer_network].peer.nfsServer}}:/cloud/local/{{main_network}} /cloud/remote/{{peer_network}} nfs rw 0 0' >> /etc/fstab
    fi
{% endif %}
{% endfor %}
}

stop()
{
    echo "SIGTERM caught, terminating NFS process(es) and shutting down wireguard interfaces..."

    /usr/sbin/exportfs -uav
    /usr/sbin/rpc.nfsd 0
    pid1=`pidof rpc.nfsd`
    pid2=`pidof rpc.mountd`
    # For IPv6 bug:
    pid3=`pidof rpcbind`
    kill -TERM $pid1 $pid2 $pid3 > /dev/null 2>&1

    wg-quick down wg0

    echo "done."
    exit
}

start()
{
    ip link del dev wg0 > /dev/null 2>&1

    wg-quick up ./wg0.conf
    
    echo "Exports:"
    cat /etc/exports

    echo "Starting rpcbind..."
    /sbin/rpcbind -w
    #echo "Displaying rpcbind status..."
    #/sbin/rpcinfo

    # Only required if v3 will be used
    # /usr/sbin/rpc.idmapd
    # /usr/sbin/rpc.gssd -v
    # /usr/sbin/rpc.statd

    echo "Starting NFS in the background..."
    /usr/sbin/rpc.nfsd --debug 8 --no-udp --no-nfs-version 2 --no-nfs-version 3
    
    echo "Exporting File System..."
    /usr/sbin/exportfs
    
    echo "Starting Mountd in the background..."These
    /usr/sbin/rpc.mountd --debug all --no-udp --no-nfs-version 2 --no-nfs-version 3
    # --exports-file /etc/exports

    # check if nfc is runnung
    pid=`pidof rpc.mountd`
    if [ -z "$pid" ]; then
      echo "Startup of NFS failed, sleeping for 2s, then retrying..."
      exit 1
    fi
}

if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

initDeviceConfig

initExports

initFstab

start

trap "stop" SIGTERM SIGINT

while true; do
    sleep 1
done

exit 1

