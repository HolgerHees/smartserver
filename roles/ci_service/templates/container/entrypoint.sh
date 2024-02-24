#!/bin/sh
 
stop()
{
    echo "Shutting down ci service"
    PID="$(pidof python3)"
    kill -s TERM $PID
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
while pidof python3 > /dev/null; do sleep 5 & wait; done

exit 1
