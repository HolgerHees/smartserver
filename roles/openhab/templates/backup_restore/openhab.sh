#!/usr/bin/bash

echo "stop openhab"
systemctl stop openhab

FOLDER=`ls -td {{backup_path}}openhab/mapdb* 2>/dev/null | head -n 1`
echo "backup folder: $FOLDER"

cp -r $FOLDER {{global_lib}}openhab/persistance/mapdb/

echo "start openhab"
systemctl start openhab
