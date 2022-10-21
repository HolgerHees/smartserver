#!/bin/bash

SSID="myssid"
PATH="/dataDisk/htdocs/guest_wifi/wifi"
APS=("xxx.xxx.xxx.xxx" "xxx.xxx.xxx.xxx")

NEW_PASSWORD="$(cat /dev/urandom | tr -dc "A-Za-z0-9" | head -c8)"

echo $NEW_PASSWORD > $PATH_$SSID.txt

for host in $APS; do
	IFACES="$(ssh root@$host 'uci show wireless' | grep \.ssid=\'$SSID\' | sed -e "s/.*\.\(.*\)\..*/\1/" | xargs)" || continue

	for i in $IFACES; do
		ssh root@$host "uci set wireless.$i.key=\"$NEW_PASSWORD\" && uci commit wireless && wifi reload" || continue 2
	done
done
