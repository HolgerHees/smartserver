#!/bin/sh
 
stop()
{
    echo "Shutting down cloud check"
    PID="$(pidof cloud_check)"
    if [ "$PID" != "" ]
    then
        kill -s TERM $PID
    fi
    wait
    exit
}

start()
{
    #/opt/shared/python/install.py

    /opt/cloud_check/cloud_check &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof cloud_check > /dev/null; do sleep 5 & wait; done

exit 1
