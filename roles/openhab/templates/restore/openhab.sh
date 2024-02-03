#!/usr/bin/bash

FOLDER=`ls -td {{backup_path}}openhab/mapdb* 2>/dev/null | head -n 1`

read -r -p "Are you sure to import '$FOLDER' into openhab mapdb? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    echo "stop openhab"
    systemctl stop openhab

    cp -r $FOLDER {{global_lib}}openhab/persistance/mapdb/

    echo "start openhab"
    systemctl start openhab
fi
