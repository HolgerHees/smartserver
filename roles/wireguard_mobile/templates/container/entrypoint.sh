#!/bin/sh
cd /etc/wireguard

stop()
{
    echo "Shutting down wireguard interfaces"
    wg-quick down wg0 2>&1
    exit
}

start()
{
    ip link del dev wg0 > /dev/null 2>&1

    wg-quick up ./wg0.conf 2>&1

    wg show | grep -q 'wg0'
    if [[ $? -eq 1 ]]; then
        >&2 echo "Interface wg0 not up"
        exit 1
    fi
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1
