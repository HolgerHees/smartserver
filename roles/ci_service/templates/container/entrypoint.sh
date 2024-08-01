#!/bin/sh
 
stop()
{
    echo "Shutting down ci service"
    PID="$(pidof ci_service)"
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

    {{global_opt}}ci_service/ci_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof ci_service > /dev/null; do sleep 5 & wait; done

exit 1
