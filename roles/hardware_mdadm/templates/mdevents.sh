#!/bin/bash

event=$1
device=$2

state=$(cat /proc/mdstat)

if [ "$event" = "Fail" ]; then
    printf "Subject: RAID: A failure has been detected on $device\n\n$state" | sendmail root
elif [ $event == "FailSpare" ]; then
    printf "Subject: RAID: A failure has been detected on spare $device\n\n$state" | sendmail root
elif [ $event == "DegradedArray" ]; then
    printf "Subject: RAID: A degraded array has been detected on $device\n\n$state" | sendmail root
elif [ $event == "TestMessage" ]; then
    printf "A test message for $device" | systemd-cat -t mdmonitor -p 6
else
    printf "Unknown $event for $device\n\n$state" | sendmail root
fi
