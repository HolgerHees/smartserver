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
#elif [ $event == "DeviceDisappeared" ]; then
#elif [ $event == "RebuildStarted" ]; then
#elif [ $event == "Rebuild20" ]; then
#elif [ $event == "Rebuild40" ]; then
#elif [ $event == "Rebuild60" ]; then
#elif [ $event == "Rebuild80" ]; then
#elif [ $event == "RebuildFinished" ]; then
#elif [ $event == "SpareActive" ]; then
#elif [ $event == "NewArray" ]; then
#elif [ $event == "MoveSpare" ]; then
#elif [ $event == "SparesMissing" ]; then
fi

