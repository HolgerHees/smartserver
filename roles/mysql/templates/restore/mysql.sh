#!/usr/bin/bash

FILE=`ls -td ./mysql/{{database}}* 2>/dev/null | head -n 1`

read -r -p "Are you sure to import '$FILE' into mysql database '{{database}}'? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    bzcat $FILE | podman exec -i mysql sh -c "mysql -u root -h 127.0.0.1 {{database}}"
{% if backup_cleanup is defined %}
    {{backup_cleanup}}
{% endif %}
fi
