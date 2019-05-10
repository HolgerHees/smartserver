#!/bin/sh

result=$(/usr/sbin/service --status-all | grep failed | sed 's/  */ /g')

if [ ! -z "$result" ]
then
  IFS=$'\n'
  for i in $result
  do
    line=$(echo "$i" | xargs)
    echo "$result"  | systemd-cat -t systemd -p 3
  done
fi
