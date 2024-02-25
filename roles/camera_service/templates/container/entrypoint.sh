#!/bin/sh
 
stop()
{
    echo "Shutting down camera service"
    PID="$(pidof camera_service)"
    kill -s TERM $PID
    wait
    exit
}

start()
{
    /opt/shared/python/install.py

    /opt/camera_service/camera_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof camera_service > /dev/null; do sleep 5 & wait; done

exit 1
