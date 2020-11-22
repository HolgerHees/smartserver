#!/bin/sh

rm -rf {{deployment_backup_path}}openhab/
mkdir {{deployment_backup_path}}openhab/
if [ -d "{{global_lib}}openhab/" ]; then
    cp -r {{global_lib}}openhab/ {{deployment_backup_path}}
fi

rm -rf {{deployment_backup_path}}mysql/
mkdir {{deployment_backup_path}}mysql/
FILE=$(ls -td {{backup_path}}mysql/nextcloud* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp $FILE {{deployment_backup_path}}mysql/
fi

FILE=$(ls -td {{backup_path}}mysql/openhab* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp $FILE {{deployment_backup_path}}mysql/
fi

rm -rf {{deployment_backup_path}}influxdb/
mkdir {{deployment_backup_path}}influxdb/
FILE=$(ls -td {{backup_path}}influxdb/openhab* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp -r $FILE/ {{deployment_backup_path}}influxdb/
fi
FILE=$(ls -td {{backup_path}}influxdb/opentsdb* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp -r $FILE/ {{deployment_backup_path}}influxdb/
fi
