#!/bin/bash

HAS_ERRORS=0

if [ -z "$LOCALNET" ]; then
    echo -e "*** No -e LOCALNET variable set. e.g. LOCALNET=\"192.168.0.0/24\""
    HAS_ERRORS=1
fi

if [ -z "$PUID" ]; then
    echo -e "*** No -e PUID variable set. e.g. PUID=\"1001\""
    HAS_ERRORS=1
fi

if [ -z "$PGID" ]; then
    echo -e "*** No -e PGID variable set. e.g. PGID=\"1001\""
    HAS_ERRORS=1
fi

if [ -z "$FLOWDUMP" ]; then
    echo -e "*** No -e FLOWDUMP variable set. e.g. FLOWDUMP=\"mysql;mysql;shared;ntopng;<user>;<pw>\""
    HAS_ERRORS=1
fi

if [ -z "$REDIS" ]; then
    echo -e "*** No -e REDIS variable set. e.g. REDIS=\"redis\""
    HAS_ERRORS=1
fi

if [ $HAS_ERRORS == 1 ]; then
    exit 1
fi

#if [ "$ACCOUNTID" ]; then
#    if [ "$LICENSEKEY" ]; then
#        echo -e "*** Found a Maxmind account and licensekey pair, ntopng will support GeoIP lookups if this is valid\nUpdating Maxmind Database"
#        echo -e "AccountID $ACCOUNTID\nLicenseKey $LICENSEKEY\nEditionIDs GeoLite2-ASN GeoLite2-City GeoLite2-Country" > /etc/GeoIP.conf
#        /usr/bin/geoipupdate
#    else
#        echo -e "*** No Maxmind GeoIP account and licensekey pair found, ntop will not support GeoIP lookups. Please get a license from maxmind.com and add as docker run -e options"
#    fi
#else
#    echo -e "*** No Maxmind GeoIP account and licensekey pair found, ntop will not support GeoIP lookups. Please get a license from maxmind.com and add as docker run -e options"
#fi

if ! id -g "ntopng" > /dev/null 2>&1; then
    addgroup -g $PUID -S ntopng
fi

if ! id -u "ntopng" > /dev/null 2>&1; then
    adduser -u $PGID -D -G ntopng -h /ntop -s /bin/false --no-create-home ntopng
fi

groupmod -o -g "$PGID" ntopng
usermod -o -u "$PUID" ntopng

echo "*** Starting netflow2ng"
su-exec ntopng /ntop/netflow2ng --listen-zmq="tcp://127.0.0.1:5556" &

echo "*** Starting ntopng"
cd /ntop/ && ./ntopng --disable-login --local-networks $LOCALNET -i tcp://127.0.0.1:5556 -F $FLOWDUMP -r $REDIS

