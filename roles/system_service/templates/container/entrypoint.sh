#!/bin/sh
 
stop()
{
    echo "Shutting down system service"
    PID="$(pidof system_service)"
    if [ "$PID" != "" ]
    then
        kill -s TERM $PID
    fi
    wait
    exit
}

start()
{
    /opt/shared/python/install.py

    /opt/system_service/system_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof system_service > /dev/null; do sleep 5 & wait; done

exit 1
