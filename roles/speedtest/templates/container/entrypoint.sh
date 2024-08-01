#!/bin/sh

stop()
{
    echo "Shutting down iperf3 service"
    PID="$(pidof iperf3)"
    if [ "$PID" != "" ]
    then
        kill -s TERM $PID
    fi
    echo "Shutting down nodejs service"
    PID="$(pidof node)"
    if [ "$PID" != "" ]
    then
        kill -s TERM $PID
    fi
    wait
    exit
}

start()
{
    # no need to wait for iperf, because we start process directly
    #ls -al /dev/stdout && iperf3 -s >> /proc/self/fd/1 2>&1 &
    iperf3 --server --forceflush &

    docker-entrypoint.sh node server.js &
    COUNTER=0; while ! pidof node > /dev/null && [ "$COUNTER" != "10" ]; do sleep 0.5 && COUNTER=$((COUNTER + 1)); done
}

start

trap "stop" SIGTERM SIGINT

# wait forever or until we get SIGTERM or SIGINT
#while :; do sleep 360 & wait; done
while pidof node > /dev/null && pidof iperf3 > /dev/null; do sleep 5 & wait; done
#while pidof node > /dev/null; do sleep 5 & wait; done

exit 1
