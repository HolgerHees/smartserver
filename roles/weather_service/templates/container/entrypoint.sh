#!/bin/sh
 
stop()
{
    echo "Shutting down weather service"
    PID="$(pidof weather_service)"
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

    /opt/weather_service/weather_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof weather_service > /dev/null; do sleep 5 & wait; done

exit 1
