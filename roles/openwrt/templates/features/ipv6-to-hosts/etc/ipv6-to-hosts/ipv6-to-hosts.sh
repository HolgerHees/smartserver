#!/bin/sh

INTERFACE=$1
DNSMASQ_LEASES=$2
DNSMASK_CONFIG=$3
STATIC_HOSTS=$4
DYNAMIC_HOSTS=$5
LOGLEVEL=$6

PIPE="/tmp/ipv6-to-hosts.pipe"

WAIT=3

CRON_TIMEOUT=60

TRAFFIC_CHECK_TIMEOUT=60
PING_CHECK_TIMEOUT=300

CLEANUP_TIMEOUT=900

DNS_CHANGED=0
LAST_CLEANUP=0

log()
{
    LEVEL=$1
    MESSAGE=$2
    if [ $1 -le $LOGLEVEL ]; then
        echo $3 $MESSAGE
    fi
}

stop()
{
    log 2 "Shutdown"
    exit 0
}

trap "stop" SIGTERM SIGINT

checkParameters(){
    if !([ -r $DNSMASQ_LEASES ]); then
        log 0 "Source file $DNSMASQ_LEASES is not readable"
        exit 1
    fi

    if !([ -r $DNSMASK_CONFIG ]); then
        log 0 "Source file $DNSMASK_CONFIG is not readable"
        exit 1
    fi

    if !([ -r $STATIC_HOSTS ]); then
        log 0 "Source file $STATIC_HOSTS is not readable"
        exit 1
    fi

    touch $DYNAMIC_HOSTS
    if !([ -w $DYNAMIC_HOSTS ]); then
        log 0 "Output file $DYNAMIC_HOSTS is not writeable"
        exit 1
    fi

    echo "Using source '${DNSMASQ_LEASES}', '${DNSMASK_CONFIG}', '$STATIC_HOSTS' and output '$DYNAMIC_HOSTS'"
}

processNeighbour(){
    DATE=$(date +%s)
    NEIGH=$(/sbin/ip -6 neigh)
    printf '%s\n' "$NEIGH" | while IFS="\n" read -r LINE
    do
        STATE=$(echo $LINE | grep -Eo "[A-z]+$")

        if [ "${STATE}" = "FAILED" ]; then
            continue
        fi

        IPV6=$(echo $LINE | cut -d " " -f 1)
        MAC=$(echo $LINE | grep -oE "lladdr [a-z0-9:]+" | cut -d " " -f 2)

        if [ "$MAC" = "" ] ; then
            continue
        fi

        if [[ "$IPV6" = fe80* ]]; then
            #echo -e "Local link detected. Skip"
            continue
        fi

        processClient $DATE $MAC $IPV6
    done
}

resolveHostname(){
    MAC=$1

    HOSTNAME=$(grep -iE -m 1 "dhcp-host=$MAC,[0-9\\.]+,.*" $DNSMASK_CONFIG | cut -d "," -f 3)
    if [ -z "$HOSTNAME" ]; then
        sleep ${WAIT}

        HOSTNAME=$(grep -iE "^[0-9]+ $MAC " $DNSMASQ_LEASES | cut -d " " -f 4)
    fi
}

refreshDNS(){
    if [ $DNS_CHANGED -eq 1 ]; then
        log 2 "DNS reloaded"
        PID=$(pidof dnsmasq | grep -oE "^[0-9]+")
        /bin/kill -HUP "$PID"
        # wait for dnsmasq to reload changes
        DNS_CHANGED=0
    fi
}

_updateClient(){
    DATE=$1
    MAC=$2
    IPV6=$3
    HOSTNAME=$4

    LINE="$IPV6 $HOSTNAME # $MAC $DATE"

    IPV6_MATCH=$(grep -E "^$IPV6 " $DYNAMIC_HOSTS)
    if [ -z "$IPV6_MATCH" ]; then
        # TODO check for different ip's for that host and check their ip
        #HOSTNAME_MATCH=$(cat $DYNAMIC_HOSTS | grep "${HOSTNAME}")
        log 2 " => added"
        printf "$LINE\n" >> $DYNAMIC_HOSTS
        DNS_CHANGED=1
    else
        LAST_UPDATE=$(echo $IPV6_MATCH | cut -d " " -f 5)
        AGE=$(($DATE-$LAST_UPDATE))

        HOST_MATCH=$(echo $IPV6_MATCH | grep " $HOSTNAME ")
        if [ -z "$HOST_MATCH" ]; then
            log 2 " => updated"
            DNS_CHANGED=1
        else
            log 2 " => refreshed"
        fi

        sed -i "s/$IPV6 .*/$LINE/" $DYNAMIC_HOSTS
    fi
}

deleteClient(){
    MAC=$1
    IPV6=$2
    HOSTNAME=$3
    TYPE=$4

    log 2 "Process '$TYPE' IPv6: $IPV6, DNS: $HOSTNAME, MAC: $MAC, State: AWAY => cleaned"
    sed -i "/^$IPV6 .*/d" $DYNAMIC_HOSTS
    DNS_CHANGED=1
}

refreshClient()
{
    DATE=$1
    MAC=$2
    IPV6=$3
    HOSTNAME=$4
    TYPE=$5

    log 2 "Process '$TYPE' IPv6: $IPV6, DNS: $HOSTNAME, MAC: $MAC, State: TCPDUMP => refreshed"

    LINE="$IPV6 $HOSTNAME # $MAC $DATE"
    sed -i "s/$IPV6 .*/$LINE/" $DYNAMIC_HOSTS
}

resolveAndUpdateClient(){
    DATE=$1
    MAC=$2
    IPV6=$3
    TYPE=$4

    HOSTNAME=""
    resolveHostname $MAC
    if [ -z "$HOSTNAME" ]; then
        log 1 "Process '$TYPE' IPv6: $IPV6, DNS: UNKNOWN, MAC: $MAC, State: TCPDUMP => skipped. MAC not found in leases and dhcp config"
    else
        log 2 "Process '$TYPE' IPv6: $IPV6, DNS: $HOSTNAME, MAC: $MAC, State: TCPDUMP" -n
        _updateClient $DATE $MAC $IPV6 $HOSTNAME
    fi
}

checkClient(){
    MAC=$1
    IPV6=$2
    HOSTNAME=$3
    AGE=$4
    STATE=$5
    TYPE=$6

    #echo $MAC
    #echo $IPV6
    #echo $HOSTNAME
    #echo $AGE
    #echo $STATE
    #echo $TYPE

    # empty MAC means FAILED state and not found in HOSTS file
    # empty HOSTNAME means not found in HOSTS file
    if [ "$STATE" = "FAILED" ] && [ -z "$HOSTNAME" ]; then
        continue
    elif [ "$STATE" != "REACHABLE" ]; then
        if [ $AGE -lt $PING_CHECK_TIMEOUT ]; then
            continue
        fi

        log 2 "Process '$TYPE' IPv6: $IPV6" -n
        ping6 -c 1 -w 1 -W 1 "$IPV6" &> /dev/null

        if [ $? -eq 0 ]; then
            STATE="PING"
        elif [ "$STATE" = "FAILED" ] && [ $AGE -lt $CLEANUP_TIMEOUT ]; then
            # start longer background ping, result will be visible next run as neighbor table result
            ping6 -c 1 -w 5 -W 5 "$IPV6" &> /dev/null &
        fi
    else
        if [ $AGE -lt $TRAFFIC_CHECK_TIMEOUT ]; then
            continue
        fi
        log 2 "Process '$TYPE' IPv6: $IPV6" -n
    fi

    if [ "$STATE" = "REACHABLE" ] || [ "$STATE" = "PING" ]; then
        if [ -z "$HOSTNAME" ]; then
            resolveHostname $MAC
            if [ -z "$HOSTNAME" ]; then
                log 2 " => skipped. MAC not found in leases and dhcp config"
                continue
            fi
        fi
        log 2 ", DNS: $HOSTNAME, MAC: $MAC, State: $STATE" -n
        _updateClient $DATE $MAC $IPV6 $HOSTNAME
    else
        if [ -z "$HOSTNAME" ]; then
            resolveHostname $MAC
            if [ -z "$HOSTNAME" ]; then
                HOSTNAME="UNKOWN"
            fi
            log 2 ", DNS: $HOSTNAME, MAC: $MAC, State: $STATE => not reachable and skipped. No host entry exists"
        else
            log 2 ", DNS: $HOSTNAME, MAC: $MAC, State: $STATE" -n
            if [ "$STATE" = "FAILED" ]; then
                if [ $AGE -gt $CLEANUP_TIMEOUT ]; then
                    log 2 " => cleaned"
                    sed -i "/^$IPV6.*/d" $DYNAMIC_HOSTS
                    DNS_CHANGED=1
                else
                    log 2 " => not reachable since $AGE seconds"
                fi
            else
                log 2 " => not reachable since $AGE seconds"
            fi
        fi
    fi
}

filterClient()
{
    IPV6=$1

    if [[ "$IPV6" = fe80* ]]; then
        return 0
    fi

    STATIC_MATCH=$(grep -E "^$IPV6 " $STATIC_HOSTS)
    if [ ! -z "$STATIC_MATCH" ]; then
        return 0
    fi

    return 1
}

checkParameters

mkfifo $PIPE
trap "rm -f $PIPE" EXIT

#10:45:56.915975 3a:95:01:6c:4b:01 > 08:91:15:8e:6b:4e, ethertype 802.1Q (0x8100), length 90: vlan 1, p 0, ethertype IPv6 (0x86dd), fe80::3895:1ff:fe6c:4b01 > fde7:1250:3eaf:10:edd8:2de8:e587:eeb7: ICMP6, neighbor solicitation, who has fde7:1250:3eaf:10:edd8:2de8:e587:eeb7, length 32
#10:45:56.917898 08:91:15:8e:6b:4e > 3a:95:01:6c:4b:01, ethertype 802.1Q (0x8100), length 82: vlan 1, p 0, ethertype IPv6 (0x86dd), fde7:1250:3eaf:10:edd8:2de8:e587:eeb7 > fe80::3895:1ff:fe6c:4b01: ICMP6, neighbor advertisement, tgt is fde7:1250:3eaf:10:edd8:2de8:e587:eeb7, length 24

#/usr/bin/tcpdump -l -e -n -i $INTERFACE '(ip6[40]=135 and src host ::) or (ip6[40]=136)' > $PIPE &
/usr/bin/tcpdump -l -e -n -i $INTERFACE '(ip6[40]=135 and src host ::) or (ip6[40]=136)' 2> /dev/stdout > $PIPE &
#/usr/bin/tcpdump -i $INTERFACE -e -n 'ip6[40]=135' -l > $PIPE &
#/usr/bin/tcpdump -i $INTERFACE -e -n 'icmp' -l > $PIPE &
exec 3<$PIPE

# https://www.fredrikholmberg.com/2012/05/ipv6-autoconfiguration-with-slaac-and-ndp-how-does-it-work/
# https://linux.die.net/man/1/nping
# https://www.cisco.com/assets/sol/sb/Switches_Emulators_v2_2_015/help/nk_configuring_ip_information11.html

READ_TIMEOUT=5
while true; do
    while read -t $READ_TIMEOUT TCPDUMP_LINE <&3; do
        #if [[ -z $TCPDUMP_LINE ]]; then
        #    break
        #fi
        log 3 "Received packet: $TCPDUMP_LINE"

        SRC_MAC=$(echo $TCPDUMP_LINE | cut -d " " -f 2)
        #DEST_MAC=$(echo $TCPDUMP_LINE | cut -d " " -f 4 | sed 's/,$//')

        #SRC_IPV6=$(echo $TCPDUMP_LINE | cut -d " " -f 17)
        #DEST_IPV6=$(echo $TCPDUMP_LINE | cut -d " " -f 19 | sed 's/:$//')

        TCPDUMP_TYPE=$(echo $TCPDUMP_LINE | grep -oE "ICMP6, neighbor [a-z]+" | cut -d " " -f 3)
        if [ "$TCPDUMP_TYPE" = "solicitation" ]; then
            _IPV6=$(echo $TCPDUMP_LINE | grep -oE "who has [0-9a-z:]+,")
            IPV6=$(echo $_IPV6 | cut -d " " -f 3 | sed 's/,$//')

            if filterClient $IPV6; then
                continue
            fi

            DATE=$(date +%s)

            resolveAndUpdateClient $DATE $SRC_MAC $IPV6 $TCPDUMP_TYPE
        elif [ "$TCPDUMP_TYPE" = "advertisement" ]; then
            _IPV6=$(echo $TCPDUMP_LINE | grep -oE "tgt is [0-9a-z:]+,")
            IPV6=$(echo $_IPV6 | cut -d " " -f 3 | sed 's/,$//')

            if filterClient $IPV6; then
                continue
            fi

            HOST_LINE=$(grep -E "^$IPV6 " $DYNAMIC_HOSTS)
            if [ -z "$HOST_LINE" ]; then
                DATE=$(date +%s)

                resolveAndUpdateClient $DATE $SRC_MAC $IPV6 $TCPDUMP_TYPE
            else
                LAST_UPDATE=$(echo $HOST_LINE | cut -d " " -f 5)
                if [ $(($DATE-$LAST_UPDATE)) -gt $TRAFFIC_CHECK_TIMEOUT ]; then
                    IPV6=$(echo $HOST_LINE | cut -d " " -f 1)
                    HOSTNAME=$(echo $HOST_LINE | cut -d " " -f 2)

                    refreshClient $DATE $SRC_MAC $IPV6 $HOSTNAME $TCPDUMP_TYPE
                fi
            fi
        #else
        #    # skipp
        fi

        TCPDUMP_LINE=""

        if [ $DNS_CHANGED -eq 1 ]; then
            READ_TIMEOUT=1
        fi
    done

    #log 2 "loop"

    refreshDNS
    READ_TIMEOUT=5

    DATE=$(date +%s)
    if [[ $(($DATE-$LAST_CLEANUP)) -gt $CRON_TIMEOUT ]]; then
        IFS=$'\n'
        for NEIGH_LINE in $(/sbin/ip -6 neigh | grep "dev $INTERFACE");
        do
            IPV6=$(echo $NEIGH_LINE | cut -d " " -f 1)
            MAC=$(echo $NEIGH_LINE | grep -oE "lladdr [a-z0-9:]+" | cut -d " " -f 2)
            STATE=$(echo $NEIGH_LINE | grep -Eo "[A-z]+$")

            if filterClient $IPV6; then
                continue
            fi

            HOST_MATCH=$(grep -E "^$IPV6 " $DYNAMIC_HOSTS)
            if [ ! -z "$HOST_MATCH" ]; then
                HOSTNAME=$(echo $HOST_MATCH | cut -d " " -f 2)
                if [ -z $MAC ]; then
                    MAC=$(echo $HOST_MATCH | cut -d " " -f 4)
                fi
                UPDATED_AT=$(echo $HOST_MATCH | cut -d " " -f 5)
                AGE=$(($DATE-$UPDATED_AT))
            else
                HOSTNAME=""
                AGE=$PING_CHECK_TIMEOUT
            fi

            checkClient "$MAC" "$IPV6" "$HOSTNAME" "$AGE" "$STATE" "neighbor job"
        done

        IFS=$'\n'
        for HOST_LINE in $(cat $DYNAMIC_HOSTS);
        do
            #echo $HOST_LINE
            IPV6=$(echo $HOST_LINE | cut -d " " -f 1)
            HOSTNAME=$(echo $HOST_LINE | cut -d " " -f 2)
            MAC=$(echo $HOST_LINE | cut -d " " -f 4)

            # Clean hosts which are not needed anymore. They are static configured now.
            if filterClient $IPV6; then
                deleteClient "$MAC" "$IPV6" "$HOSTNAME" "host job"
                continue
            fi

            MATCH=$(/sbin/ip -6 neigh show $IPV6 | grep -E "^$IPV6 ")
            if [ $? -eq 0 ] && [ -z $MATCH ]; then
                UPDATED_AT=$(echo $HOST_LINE | cut -d " " -f 5)
                AGE=$(($DATE-$UPDATED_AT))

                checkClient "$MAC" "$IPV6" "$HOSTNAME" "$AGE" "FAILED" "host job"
            fi
        done

        LAST_CLEANUP=$DATE
        refreshDNS
    fi

    #log 2 "loop"
done
