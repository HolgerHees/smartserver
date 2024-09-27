#!/usr/bin/bash

FILE=`ls -td ./mariadb/{{database}}* 2>/dev/null | head -n 1`

read -r -p "Are you sure to import '$FILE' into mariadb database '{{database}}'? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    bzcat $FILE | podman exec -i mariadb mariadb -u root -h 127.0.0.1 {{database}}
{% if backup_cleanup is defined %}
    {{backup_cleanup}}
{% endif %}
fi
