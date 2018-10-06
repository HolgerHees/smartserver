#!/bin/bash
DIRNAME=`dirname "$0"`

RESULT=`/usr/bin/vclient -h 127.0.0.1:3002 -f ${DIRNAME}/heizung.cmd -t ${DIRNAME}/heizung.tpl 2>&1`
CODE=${PIPESTATUS[0]}

#while true; do
while false; do

    RESULT=`/usr/bin/vclient -h 127.0.0.1:3002 -f ${DIRNAME}/heizung.cmd -t ${DIRNAME}/heizung.tpl 2>&1`
    CODE=${PIPESTATUS[0]}

    #echo $STATUS
    #echo $RESULT

    exit
    
    # || [[ $RESULT == *Fehler\ send,\ Abbruch* ]]
    if [ "$CODE" -ne 0 ] || [ -z "$RESULT" ]; then

        printf "STATUS: %s\nRESULT: %s" "$CODE" "$RESULT" > "{{global_log}}/heizung/Heizungslesefehler_$(date +"%d.%m.%Y_%H:%M:%S")"

        if [[ $(pidof vcontrold | wc -w) > 0 ]]; then

            curl -s -X PUT -H "Content-Type: text/plain" -d 990 "http://127.0.0.1:8080/rest/items/Heating_Common_Fault/state"

            /usr/bin/systemctl stop vcontrold
        
            #screen -X -S usbmon quit
        
            #logfile="{{global_log}}usbmon/bus1.mon.out"
            #if [ -f "$logfile" ]
            #then
                #suffix=$(date +".error_%Y.%m.%d_%H:%M:%S")
                #mv $logfile $logfile$suffix
            #fi
            
            #suffix=$(date +".error_%Y.%m.%d_%H:%M:%S")
            #logfile="{{global_log}}usbdebug/messages"
            #cp /var/log/messages $logfile$suffix

            #screen -dmS usbmon bash -c "cat /sys/kernel/debug/usb/usbmon/1u > $logfile"
            vidpid="0403:6001"
            bus_dev=`lsusb | grep "ID\s$vidpid" | sed 's/^.*Bus\s\([0-9]\+\)\sDevice\s\([0-9]\+\).*$/\1\/\2/g' | tail -n 1` 
            bus_path="/dev/bus/usb/$bus_dev"

            RESET_RESULT=`/opt/usbreset/usbreset $bus_path 2>&1`
            #echo $RESET_RESULT

            sleep 120
        fi

        /usr/bin/systemctl start vcontrold

        sleep 10
    else

        break;
    fi
done

hasError=0
while IFS='|' read -r item value status; do
    if [ -z "$value" ] || [ -z "$status" ] || [[ ${status:0:2} != "OK" ]]; then
        hasError=1
    else
        #echo $item
        curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://127.0.0.1:8080/rest/items/"$item"/state"
    fi
done <<< "$RESULT"

if [ "$hasError" -eq 1 ]; then
    printf "STATUS: %s\nRESULT: %s" "$CODE" "$RESULT" > "{{global_log}}/heizung/Heizungsdatenfehler_$(date +"%d.%m.%Y_%H:%M:%S")"
fi
