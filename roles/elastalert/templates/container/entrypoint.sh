#!/bin/sh


stop()
{
    echo "INFO:elastalert:Shutting down"
    killall elastalert
    exit
}

trap "stop" SIGTERM SIGINT

/usr/bin/elastalert --verbose --rule /etc/elastalert/rule.yaml --config /etc/elastalert/config.yaml 2>&1 &

# wait forever or until we get SIGTERM or SIGINT
while :; do
    ps -f -o pid,comm | grep elastalert > /dev/null;
    if [ $? -ne 0 ] ; then
        break;
    fi
    
    sleep 60 & wait; 
done

exit 1
