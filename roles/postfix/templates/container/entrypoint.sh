#!/bin/sh

newaliases

rm -f /var/spool/postfix/pid/*.pid

/build/postfix_exporter/postfix_exporter --postfix.logfile_path /dev/stdout --web.listen-address :80 2>&1 &
P1=$!

postfix -c /etc/postfix start-fg &
P2=$!

wait $P1 $P2

#exec postfix -c /etc/postfix start-fg
 
