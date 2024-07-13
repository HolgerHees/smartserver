#!/bin/sh

export PATH="/sbin:/bin:/usr/sbin:/usr/bin"

collectRules() {
    #RESULT=$(iptables -S $1 | grep SMARTSERVER | cut -c4-)
    RESULT=$(iptables -S $1 | grep NETAVARK | cut -c4-)
    echo "$RESULT"
}

if [ "$1" == "check" ]; then
    RESULT1=$(collectRules INPUT)
    RESULT2=$(collectRules FORWARD)
    if [ -n "$RESULT1" ] || [ -n "$RESULT2" ]; then
        NOW=$(date +%s)
        RESULT=$(podman ps --format '{{.StartedAt}}')
        IFS=$'\n'
        for StartedAt in $RESULT
        do
            DIFF=`expr $NOW - $StartedAt`
            if [ "$DIFF" -lt "5" ]; then
                "Ignore rule leftovers after a new container start"
                exit 0
            fi
        done

        echo "NETAVARK rules active"
        exit 1
    fi
else
    RESULT=$(collectRules INPUT)
    IFS=$'\n'
    for rule in $RESULT
    do
        CMD=$(echo "iptables -D $rule")
        #echo $CMD
        eval $CMD
    done

    RESULT=$(collectRules FORWARD)
    IFS=$'\n'
    for rule in $RESULT
    do
        CMD=$(echo "iptables -D $rule")
        #echo $CMD
        eval $CMD
    done
fi
