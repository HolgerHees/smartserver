#!/bin/sh
 
is_running=0

stop()
{
    is_running=0
    
    echo "Shutting down weather service"
    PID="$(pidof weather_service)"
    if [ "$PID" != "" ]
    then
        kill -s TERM $PID
    fi
    wait
    exit 0
}

start()
{
    is_running=1
    
    /opt/shared/python/install.py

    /opt/weather_service/weather_service &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof weather_service > /dev/null; do sleep 5 & wait; done

if [ "$is_running" -eq 1 ]; then
    exit 1
fi
