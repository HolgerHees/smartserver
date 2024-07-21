#!/usr/bin/sh

if [ -x /usr/sbin/iptables ]; then
    /usr/sbin/iptables -t nat -F
    /usr/sbin/iptables -t mangle -F
    /usr/sbin/iptables -t filter -F
    /usr/sbin/iptables -t raw -F

    /usr/sbin/iptables -t nat -X
    /usr/sbin/iptables -t mangle -X
    /usr/sbin/iptables -t filter -X
    /usr/sbin/iptables -t raw -X
fi
