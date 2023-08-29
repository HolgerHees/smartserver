#!/bin/sh
 
stop()
{
    echo "Shutting iperf3 service"
    PID="$(pidof iperf3)"
    kill -s TERM $PID

    echo "Shutting down system service"
    PID="$(pidof node)"
    kill -s TERM $PID
    wait
    exit
}

start()
{
    docker-entrypoint.sh node server.js &
    iperf3 -s &
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof node > /dev/null && pidof iperf3 > /dev/null; do sleep 5 & wait; done

exit 1
