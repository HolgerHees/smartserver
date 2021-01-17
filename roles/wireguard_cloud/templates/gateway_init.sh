#!/bin/sh
/usr/bin/nsenter -n -t $(/usr/bin/docker inspect --format {{'{{'}}.State.Pid{{'}}'}} {{container_name}}) /usr/sbin/ip route del default
/usr/bin/nsenter -n -t $(/usr/bin/docker inspect --format {{'{{'}}.State.Pid{{'}}'}} {{container_name}}) /usr/sbin/ip route add default via {{gateway}}
