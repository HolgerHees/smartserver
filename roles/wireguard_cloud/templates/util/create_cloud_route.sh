#!/bin/sh

if /usr/sbin/ip route list | grep -q "{{vpn_cloud_subnet}}.0.0/16"; then
  ip route del {{vpn_cloud_subnet}}.0.0/16
fi

ip route add {{vpn_cloud_subnet}}.0.0/16 via {{vpn_cloud_services.local.gateway}}
