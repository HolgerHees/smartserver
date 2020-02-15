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
  /opt/netdata_helper/inform_openhab
  sleep 60
  rm {{global_tmp}}netdata_notification.lock
}

if [ ! -f "{{global_tmp}}netdata_notification.lock" ] || [ -n "$(find {{global_tmp}} -name netdata_notification.lock -mmin +1)" ]; then
  notify_openhab &
else 
  echo "Openhab notification not possible"  | systemd-cat -t netdata -p "warning"
fi
