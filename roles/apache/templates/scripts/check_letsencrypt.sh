#!/usr/bin/sh

EMAIL="{{root_email}}"
SERVER="{{server_domain}}"
HTDOCS="{{htdocs_path}}"
ETC="{{global_etc}}"
DOMAINS=`grep -ohP "ServerName\s*\K(.+)\.$SERVER" ${ETC}apache2/_.ansible.vhost.d/*.conf`
#UNIQUE_DOMAINS=`echo $DOMAINS | tr ' ' '\n' | sort -u | tr '\n' ' '| xargs | sed -e 's/ / -d /g'`
UNIQUE_DOMAINS=`echo $DOMAINS | tr ' ' '\n' | sort -u | tr '\n' ' '| xargs | sed -e 's/ / -d /g'`

if [ $# -gt 0 ] & [ "$1" == "update" ]
then
  LETSENCRYPT_CMD="podman exec apache2 sh -c \"certbot certonly --webroot -w ${HTDOCS}_public --preferred-challenges http --agree-tos --email $EMAIL --cert-name $SERVER -d $SERVER -d $UNIQUE_DOMAINS\""

  printf "\n\n"

  eval $LETSENCRYPT_CMD
else
  LETSENCRYPT_CMD="podman exec apache2 sh -c \"certbot certonly --webroot -w ${HTDOCS}_public --dry-run --preferred-challenges http --agree-tos --email $EMAIL --cert-name $SERVER -d $SERVER -d $UNIQUE_DOMAINS\""

  echo $LETSENCRYPT_CMD

  printf "\n\n"

  eval $LETSENCRYPT_CMD
fi
