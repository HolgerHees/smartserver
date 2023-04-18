#!/bin/sh

if /usr/sbin/ethtool mac0 2>/dev/null | grep -q "Link detected"; then
  ip link del mac0
fi

ip link add mac0 link {{default_network_interface}} type macvlan mode bridge
ip addr add {{default_server_ip}}/32 dev mac0
ip link set mac0 up
ip route add {{macvlan_range}} dev mac0

sysctl -w net.ipv6.conf.mac0.autoconf=0
