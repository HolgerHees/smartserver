#!/bin/sh
 
stop()
{
    echo "Shutting system service"
    killall python3
    exit
}

start()
{
    /opt/shared/python/install.py

    /etc/system_service/system_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof python3 > /dev/null; do sleep 5 & wait; done

exit 1
