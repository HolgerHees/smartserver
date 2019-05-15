#!/bin/sh

message=$3

case $2 in
"local6.info")
  level="info"
  ;;
"local6.warning")
  level="warning"
  ;;
"local6.crit")
  level="crit"
  ;;
*)
  level="crit"
  message="UNKOWN LEVEL $2 : $message"
  ;;
esac

#line=$(echo "$i" | xargs)
echo "$message"  | systemd-cat -t system -p $level
