#!/bin/sh

rm -rf {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/openhab/
mkdir {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/openhab/
if [ -d "{{global_lib}}openhab/" ]; then
    cp -r {{global_lib}}openhab/ {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/
fi

rm -rf {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/mysql/
mkdir {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/mysql/
FILE=$(ls -td {{local_backup_path}}mysql/nextcloud* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp $FILE {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/mysql/
fi

FILE=$(ls -td {{local_backup_path}}mysql/openhab* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp $FILE {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/mysql/
fi

rm -rf {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/influxdb/
mkdir {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/influxdb/
FILE=$(ls -td {{local_backup_path}}influxdb/openhab* 2>/dev/null | head -n 1)
if [ ! -z $FILE ]; then
    cp -r $FILE/ {{projects_path}}{{ansible_project_name}}/{{config_path}}backup/influxdb/
fi
