#!/bin/sh
cd /etc/wireguard

stop()
{
    echo "Shutting down wireguard interfaces"
    wg-quick down wg0
    exit
}

start()
{
    ip link del dev wg0 > /dev/null 2>&1

    wg-quick up ./wg0.conf
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1
