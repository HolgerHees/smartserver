#!/bin/sh
cd /etc/wireguard

#https://wiki.archlinux.org/index.php/NFS/Troubleshooting

#rpcdebug -m nfsd all

#https://www.heise.de/ct/artikel/NFSv4-unter-Linux-221582.html?seite=all
# check cat /proc/net/rpc/auth.unix.ip/content

initDeviceConfig()
{
    PRIVATE_KEY=$(cat ./keys/server_privatekey)

    NEW_CONFIG="[Interface]
PrivateKey = ${PRIVATE_KEY}
Address = {{cloud_network.interface.address}}
ListenPort = {{exposed_port}}
SaveConfig = true

{% for peer_name in cloud_network.peers %}
[Peer]
PublicKey = {{cloud_network.peers[peer_name].publicKey}}
AllowedIPs = {{cloud_network.peers[peer_name].allowedIPs}}
Endpoint = {{cloud_network.peers[peer_name].endpoint}}
PersistentKeepalive = 25
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
    NEW_EXPORTS="{% for peer_name in cloud_network.peers %}
/cloud/export/{{peer_name}} {{cloud_network.peers[peer_name].allowedIPs}}(fsid=0,rw,sync,no_root_squash,no_subtree_check)
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
{% for peer_name in cloud_network.peers %}
    if ! grep -q '{{cloud_network.peers[peer_name].nfsServer}}' /etc/fstab ; then
        #echo '{{cloud_network.peers[peer_name].nfsServer}}:/cloud/export/{{main_network}} /cloud/mount/{{peer_name}} nfs nfsvers=4.2,rw,noauto,rsize=8192,wsize=8192 0 0' >> /etc/fstab
        echo '{{cloud_network.peers[peer_name].nfsServer}}:/ /cloud/mount/{{peer_name}} nfs nfsvers=4.2,rw,noauto,rsize=8192,wsize=8192 0 0' >> /etc/fstab
    fi
{% endfor %}
}

mountShares()
{
{% for peer_name in cloud_network.peers %}
    peer_ip_{{peer_name}}='{{cloud_network.peers[peer_name].nfsServer}}'
{% endfor %}
    peers="{% for peer_name in cloud_network.peers %}{{peer_name}} {% endfor %}"

    echo "mount nfs shares..."
    x=1
    while :
    do
        mount_state=0
        
        for name in $peers
        do
            if [ ! $(mountpoint -q /cloud/mount/$name) ]
            then
                eval "peer_ip=\$peer_ip_$name"
                echo "check reachability of $peer_ip"
                nc -w 1 -z $peer_ip 2049
                STATUS=$( echo $? )
                if [[ $STATUS == 0 ]]
                then
                    echo "mount /cloud/mount/$name"
                    mount /cloud/mount/$name
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
            
            if [ $x -gt 30 ]
            then
                echo "...giving up"
                break
            fi
        fi
    done
}

stop()
{
    echo "SIGTERM caught, shutting down..."
    
    echo "unmount nfs shares"
{% for peer_name in cloud_network.peers %}
    echo "unmount /cloud/mount/{{peer_name}}"
    umount -f -l /cloud/mount/{{peer_name}} > /dev/null 2>&1
{% endfor %}

    echo "terminating nfs process(es)"
    /usr/sbin/exportfs -uav
    /usr/sbin/rpc.nfsd 0
    pid1=`pidof rpc.nfsd`
    pid2=`pidof rpc.mountd`
    #pid3=`pidof rpc.statd`
    # For IPv6 bug:
    #pid4=`pidof rpcbind`
    #kill -TERM $pid1 > /dev/null 2>&1
    kill -TERM $pid1 $pid2 > /dev/null 2>&1

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
    #echo "starting rpcbind"
    #/sbin/rpcbind -w
    #echo "starting idmapd"
    #/usr/sbin/rpc.idmapd
    #echo "starting statd"
    #/sbin/rpc.statd
    ##-p 32765 -o 32766
    
    # Kerberos
    #/usr/sbin/rpc.svcgssd -v
    #/usr/sbin/rpc.gssd -v
    
    echo "starting nfs"
    /usr/sbin/rpc.nfsd --debug --no-nfs-version 2 --no-nfs-version 3
    #sleep 1
    #/usr/sbin/rpc.nfsd 0
    #sleep 1
    #/usr/sbin/rpc.nfsd --debug --no-nfs-version 2
    
    echo "starting exportfs"
    FS_RESULT=$(/usr/sbin/exportfs -arv)
    if [ -z "$FS_RESULT" ]
    then
      echo "export validation failed"
      exit 1
    else
      echo $FS_RESULT
    fi
    
    #echo "starting mountd"
    /usr/sbin/rpc.mountd --debug all --no-nfs-version 2 --no-nfs-version 3
    # --exports-file /etc/exports

    # check if nfc is running
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

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1

