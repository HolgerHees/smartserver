#!/usr/bin/bash

FOLDER=`ls -td {{backup_path}}influxdb/{{database}}* 2>/dev/null | head -n 1`
FOLDER_NAME="$(basename -- $FOLDER)"

read -r -p "Are you sure to import '$FOLDER' into influxdb database '{{database}}'? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    docker exec influxdb sh -c "influxd restore --bucket {{database}} --org default-org /var/lib/influxdb/data /var/lib/influxdb_backup/$FOLDER_NAME"
fi
