#!/bin/sh
cd /etc/wireguard

#https://wiki.archlinux.org/index.php/NFS/Troubleshooting

#rpcdebug -m nfsd all

initDeviceConfig()
{
    PRIVATE_KEY=$(cat ./keys/server_privatekey)

    NEW_CONFIG="[Interface]
PrivateKey = ${PRIVATE_KEY}
Address = {{cloud_network.interface.address}}
ListenPort = {{exposed_port}}
SaveConfig = true

{% for peer_name in vpn_peers %}
[Peer]
PublicKey = {{vpn_peers[peer_name].publicKey}}
AllowedIPs = {{vpn_peers[peer_name].allowedIPs}}
Endpoint = {{vpn_peers[peer_name].endpoint}}
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
    NEW_EXPORTS="{% for peer_name in vpn_peers %}
/cloud/local/{{peer_name}} {{vpn_peers[peer_name].allowedIPs}}(rw,no_root_squash,sync,no_subtree_check)
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
{% for peer_name in vpn_peers %}
    if ! grep -q '{{vpn_peers[peer_name].nfsServer}}' /etc/fstab ; then
        echo '{{vpn_peers[peer_name].nfsServer}}:/cloud/local/{{main_network}} /cloud/remote/{{peer_name}} nfs rw 0 0' >> /etc/fstab
    fi
{% endfor %}
}

mountShares()
{
{% for peer_name in vpn_peers %}
    peer_ip_{{peer_name}}='{{vpn_peers[peer_name].nfsServer}}'
{% endfor %}
    peers={% for peer_name in vpn_peers %}{{peer_name}} {% endfor %}

    echo "mount nfs shares..."
    x=1
    while [ $x -le 30 ]
    do
        mount_state=0
        
        for name in $peers
        do
            if [ ! $(mountpoint -q /cloud/remote/$name) ]
            then
                eval "peer_ip=\$peer_ip_$name"
                echo "check reachability of $peer_ip"
                nc -w 1 -z $peer_ip 111
                STATUS=$( echo $? )
                if [[ $STATUS == 0 ]]
                then
                    echo "mount /cloud/remote/$name"
                    mount /cloud/remote/$name
                else
                    mount_state=1
                fi
            fi
        done
        
        if [ $mount_state == 0 ]
        then
            echo "...done"
            break
        else
            sleep 1
            x=$(( $x + 1 ))
        fi
    done
}

stop()
{
    echo "SIGTERM caught, shutting down..."
    
    echo "unmount nfs shares"
{% for peer_name in vpn_peers %}
    echo "unmount /cloud/remote/{{peer_name}}"
    umount -f -l /cloud/remote/{{peer_name}} > /dev/null 2>&1
{% endfor %}

    echo "terminating nfs process(es)"
    /usr/sbin/exportfs -uav
    /usr/sbin/rpc.nfsd 0
    pid1=`pidof rpc.nfsd`
    pid2=`pidof rpc.mountd`
    #pid3=`pidof rpc.statd`
    # For IPv6 bug:
    pid3=`pidof rpcbind`
    kill -TERM $pid1 $pid2 $pid3 > /dev/null 2>&1

    echo "shutting down wireguard interface"
    wg-quick down wg0

    echo "done"
    exit
}

start()
{
    ip link del dev wg0 > /dev/null 2>&1

    echo "starting container..."

    #echo "exported folder"
    #cat /etc/exports

    echo "setting up wireguard interface"
    wg-quick up ./wg0.conf
    
    #echo "open nlockmgr ports"
    #mount -t nfsd nfsd /proc/fs/nfsd
    #echo 'fs.nfs.nlm_tcpport=32768' >> /etc/sysctl.conf
    #echo 'fs.nfs.nlm_udpport=32768' >> /etc/sysctl.conf
    #sysctl -p > /dev/null
    
    # Normally only required if v3 will be used
    # But currently enabled to overcome an NFS bug around opening an IPv6 socket
    echo "starting rpcbind"
    /sbin/rpcbind -w
    #echo "Displaying rpcbind status..."
    #/sbin/rpcinfo

    # /usr/sbin/rpc.idmapd
    # /usr/sbin/rpc.gssd -v
    #echo "starting statd"
    #/usr/sbin/rpc.statd
    #-p 32765 -o 32766
    
    echo "starting nfs"
    /usr/sbin/rpc.nfsd --debug
    #--no-udp --no-nfs-version 2 --no-nfs-version 3
    
    echo "starting exportfs"
    FS_RESULT=$(/usr/sbin/exportfs -rv)
    if [ -z "$FS_RESULT" ]
    then
      echo "export validation failed"
      exit 1
    else
      echo $FS_RESULT
    fi
    
    echo "starting mountd"
    /usr/sbin/rpc.mountd --debug all
    #--no-udp --no-nfs-version 2 --no-nfs-version 3
    # --exports-file /etc/exports

    # check if nfc is runnung
    pid=`pidof rpc.mountd`
    if [ -z "$pid" ]; then
      echo "startup of nfs failed"
      exit 1
    fi
    
    echo "...done"
}

if [ ! -f ./keys/server_privatekey ] || [ ! -f ./keys/server_publickey ]
then
    wg genkey | tee ./keys/server_privatekey | wg pubkey > ./keys/server_publickey
fi

trap "stop" SIGTERM SIGINT

initDeviceConfig

initExports

initFstab

start

mountShares

while true
do
    sleep 1
done

exit 1

