#!/bin/sh

exitcode=1
watched_pids=""

stop()
{
    echo "Entrypoint - Shutting down service"

    exitcode=0

    echo "Entrypoint - Send 'TERM' to pid(s) '$watched_pids'"
    kill -s TERM $watched_pids

    echo "Entrypoint - Wait for pid(s) '$watched_pids'"
    wait $watched_pids

    echo "Entrypoint - Exit $exitcode"
    exit $exitcode
}

start()
{
    echo "Entrypoint - Starting service"
{% for cmdline in entrypoint_services %}
    {{ cmdline }}
{% if cmdline[-2:] == ' &' %}
    PID=$!
    watched_pids="$watched_pids $PID"
{% endif %}
{% endfor %}

    watched_pids=$(echo $watched_pids | xargs)

    echo "Entrypoint - Service started with pid(s) '$watched_pids'"
}

start

trap "stop" SIGTERM SIGINT

if [ ! -z "$watched_pids" ]; then
    echo "Entrypoint - Observe pid(s) '$watched_pids'"

    IFS=' '
    CMD=""
    for pid in $watched_pids
    do
        if [ ! -z "$CMD" ]; then
            CMD="$CMD &&"
        fi
        CMD="$CMD test -d /proc/$pid/"
    done

    #echo "Entrypoint - CMD: '$CMD'"
    while eval "$CMD"; do sleep 5 & wait $!; done
    #while true; do wait $watched_pids; break; done
fi

if [ $exitcode -ne 0 ]; then
    echo "Entrypoint - Unexpected interruption with code '$exitcode'"
fi

exit $exitcode
