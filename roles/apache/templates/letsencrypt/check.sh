#!/usr/bin/bash

DOMAINS=`grep -ohP "ServerName\s*\K(.*){{server_domain}}" {{global_etc}}apache2/_.ansible.vhost.d/*.conf`
UNIQUE_DOMAINS=`echo $DOMAINS | tr ' ' '\n' | sort -u | tr '\n' ' '| xargs | sed -e 's/ / -d /g'`

LETSENCRYPT_CMD="docker exec apache2 sh -c \"certbot certonly --webroot -w /dataDisk/htdocs/letsencrypt --dry-run --preferred-challenges http --agree-tos --email holger.hees@gmail.com -d $UNIQUE_DOMAINS\""

echo $LETSENCRYPT_CMD

printf "\n\n"

eval $LETSENCRYPT_CMD
