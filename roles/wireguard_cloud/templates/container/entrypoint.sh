#!/bin/sh

exitcode=1

cd /etc/wireguard

#https://wiki.archlinux.org/index.php/NFS/Troubleshooting

#rpcdebug -m nfsd all

#https://www.heise.de/ct/artikel/NFSv4-unter-Linux-221582.html?seite=all
# check cat /proc/net/rpc/auth.unix.ip/content

stop()
{
    echo "Entrypoint - Shutting down wireguard interface"

    exitcode=0

    wg-quick down wg0 2>&1

    exit $exitcode
}

start()
{
    echo "Entrypoint - Starting wireguard interface"

    ip link del dev wg0 > /dev/null 2>&1

    #echo "exported folder"
    #cat /etc/exports

    wg-quick up ./wg0.conf 2>&1

    wg show | grep -q 'wg0'
    if [[ $? -eq 1 ]]; then
        >&2 echo "Entrypoint - Interface wg0 not up"
        exit 1
    fi
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
while wg show | grep -q 'wg0'; do sleep 60 & wait $!; done

if [ $exitcode -ne 0 ]; then
    echo "Entrypoint - Entrypoint - Unexpected interruption with code '$exitcode'"
fi

exit $exitcode


