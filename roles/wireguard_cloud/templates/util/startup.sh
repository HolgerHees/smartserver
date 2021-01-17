#!/bin/sh
cd /etc/wireguard

#https://wiki.archlinux.org/index.php/NFS/Troubleshooting

#rpcdebug -m nfsd all

#https://www.heise.de/ct/artikel/NFSv4-unter-Linux-221582.html?seite=all
# check cat /proc/net/rpc/auth.unix.ip/content

stop()
{
    echo "SIGTERM caught, shutting down..."
    
    echo "shutting down wireguard interface"
    wg-quick down wg0

    echo "done"
    exit
}

startWireguard()
{
    ip link del dev wg0 > /dev/null 2>&1

    #echo "exported folder"
    #cat /etc/exports

    echo "setting up wireguard interface"
    wg-quick up ./wg0.conf
}

trap "stop" SIGTERM SIGINT

startWireguard

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1

