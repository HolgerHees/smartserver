#!/usr/bin/bash

. /opt/helper/_config

COLLECT_CMD=$(printf 'grep -ohP "ServerName\s*\K(.*)%s" %sapache2/_.ansible.vhost.d/*.conf' $SERVER_DOMAIN $ETC_PATH)
COLLECTED_DOMAINS=`eval $COLLECT_CMD`

UNIQUE_DOMAINS=`echo $COLLECTED_DOMAINS | tr ' ' '\n' | sort -u | tr '\n' ' '| xargs | sed -e 's/ / -d /g'`

LETSENCRYPT_CMD=$(printf 'docker exec apache2 sh -c "certbot certonly --webroot -w %sletsencrypt --dry-run --preferred-challenges http --agree-tos --email %s -d %s"' $HTDOCS_PATH $SERVER_EMAIL "$UNIQUE_DOMAINS")

echo $LETSENCRYPT_CMD

printf "\n\n"

eval $LETSENCRYPT_CMD
