#!/bin/sh

newaliases

rm -f /var/spool/postfix/pid/*.pid

exec postfix -c /etc/postfix start-fg
 
