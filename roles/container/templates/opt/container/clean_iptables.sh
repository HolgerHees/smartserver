#!/bin/sh

RESULT=$(iptables -S INPUT | grep NETAVARK | cut -c4-)
if [ -n "$RESULT" ]; then
    CMD=$(echo "iptables -D $RESULT")
    eval $CMD
fi

RESULT=$(iptables -S FORWARD | grep NETAVARK | cut -c4-)
if [ -n "$RESULT" ]; then
    CMD=$(echo "iptables -D $RESULT")
    eval $CMD
fi
