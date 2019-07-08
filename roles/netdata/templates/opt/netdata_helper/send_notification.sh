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

notify_openhab()
{
  touch {{global_tmp}}netdata_notification.lock
  /usr/bin/php -f /opt/netdata_helper/inform_openhab.php
  sleep 60
  rm {{global_tmp}}netdata_notification.lock
}

if [ ! -f "{{global_tmp}}netdata_notification.lock" ]; then
  notify_openhab &
else 
  echo "Openhab notification not possible"  | systemd-cat -t system -p "warning"
fi
