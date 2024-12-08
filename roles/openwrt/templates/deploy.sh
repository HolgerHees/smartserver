#!/bin/bash

execute() {
  if [ -z "$1" ]
  then
    echo "Nothing to execute"
    RETCODE=0
  fi

  COMMAND=$@

  if [ "$SSHAUTH" == "password" ]
  then
    echo "Execute " $COMMAND
    sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP $COMMAND
    RETCODE=$?
  elif [ "$SSHAUTH" == "publickey" ]
  then
    echo "Execute " $COMMAND
    ssh $HOSTNAME $COMMAND
    RETCODE=$?
  else
    RETCODE=-1
  fi
  unset COMMAND
  return $RETCODE
}

execute_scp() {
  if [ "$SSHAUTH" == "password" ]
  then
    COMMAND="scp -rp $SOURCE/$IP/* root@$IP:/"
    echo "Execute " $COMMAND
    sshpass -f <(printf '%s\n' $PASSWORD) $COMMAND
  elif [ "$SSHAUTH" == "publickey" ]
  then
    COMMAND="scp -rp $SOURCE/$IP/* $HOSTNAME:/"
    echo "Execute " $COMMAND
    $COMMAND
  fi

  unset COMMAND
}

authenticate() {
  N=5
  for i in $(seq 1 $N); do
    if [ "$SSHAUTH" == "password" ]
    then
      echo -n "Enter password": 
      read -s PASSWORD
      echo
    fi
    
    echo -n "Authenticate ... "
    execute "/bin/true"
    
    EXIT_CODE=`echo $?`
    
    if [ "$EXIT_CODE" -eq 6 ]
    then
      echo "unknown key fingerprint."
      echo "Login manually first"
      exit
    elif [ "$EXIT_CODE" -eq 0 ]
    then
      echo "ok"
      break
    else
      unset PASSWORD
    fi
  done
  
  if test "$SSHAUTH" == "password" && test -z "$PASSWORD"
  then
    echo "Exit... Got no valid password after $N retries."
    exit
  fi
}

connectivity() {
  N=5
  for i in $(seq 1 $N); do
    if [ -z "$IP" ]
    then
      echo -n "Enter IP adress": 
      read IP
    fi
    
    echo -n "Check connectivity ... "
    ping -c1 -W 1 $IP > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
      echo "ok"
      break
    else
      echo "IP address not reachable"
      unset IP
    fi
  done
  
  if [ -z "$IP" ]
  then
    echo "Exit... Got no valid IP address after $N retries."
    exit
  fi
}

if [[ -n $1 ]]; then
  IP=$1
fi

connectivity

SOURCE=`dirname "$0"`
if [ ! -f "$SOURCE/$IP.env" ]; then
    echo "Exit... Configuration for IP $IP does not exists."
    exit
fi

source "$SOURCE/$IP.env"

authenticate

TZ=`tail -1 "/usr/share/zoneinfo/$TIMEZONE"`

echo "Refresh package lists ..."
execute "opkg update > /dev/null"

if [[ "$INSTALL_PACKAGES" != "" ]]; then
  echo "Install packages ..."
  execute "opkg install" $INSTALL_PACKAGES " > /dev/null"
fi

if [[ "$REMOVE_PACKAGES" != "" ]]; then
  echo "Uninstall packages ..."
  execute "opkg remove" $REMOVE_PACKAGES " > /dev/null"
fi

if [[ "$IS_AP" == 1 ]]; then
  echo "Install wifi packages ..."
  execute "opkg remove wpad-basic-wolfssl wpad-basic-mbedtls > /dev/null"
  execute "opkg install wpad-wolfssl hostapd-utils > /dev/null"

  grep "ieee80211r '1'" "$SOURCE/$IP/etc/config/wireless" > /dev/null
  if [ $? -eq 0 ]; then
    echo "Install roaming packages ..."
    execute "opkg install umdns dawn luci-app-dawn > /dev/null"
    execute "[ -f /etc/seccomp/umdns.json ] && mv /etc/seccomp/umdns.json /etc/seccomp/umdns.json.disabled"
  fi
fi

echo "Copy configs ..."
execute_scp

#authenticate

echo "Apply hostname and timezone ..."
execute "uci set system.@system[0].hostname='$HOSTNAME' & uci commit system;"
execute "uci set system.@system[0].zonename='$TIMEZONE' & uci set system.@system[0].timezone='$TZ' & uci commit system & /etc/init.d/system reload;"

echo "Force web redirect ..."
execute "uci set uhttpd.main.redirect_https='on' & uci commit uhttpd;"

if [[ "$ENABLED_SERVICES" != "" ]]; then
  read -ra SERVICES <<< "$ENABLED_SERVICES"
  for SERVICE in "${SERVICES[@]}";
  do
    echo "Enable and start $SERVICE ..."
    execute "/etc/init.d/$SERVICE enable & /etc/init.d/$SERVICE start"
  done
fi


#/etc/init.d/rpcd restart
#/etc/init.d/snmpd restart

# disabled upgrades, because they are using too much additional flash space
#echo "Search for upgrades ..."
#AVAILABLE_UPDATES_RESULT=$(sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "opkg list-upgradable")

#if [[ "$AVAILABLE_UPDATES_RESULT" != "" ]]; then
#  AVAILABLE_UPDATES=$(echo "$AVAILABLE_UPDATES_RESULT" | wc -l)
#  echo -n "$AVAILABLE_UPDATES Updates available. Run upgrade packages? [y/N]":
#  read UPGRADE

#  if [[ $UPGRADE =~ ^[Yy]$ ]]; then
#    echo "Upgrading now ..."
#    sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "opkg list-upgradable | cut -f 1 -d ' ' | xargs -r opkg upgrade; > /dev/null"
#  fi
#fi

echo -n "Reboot now? [y/N]": 
read REBOOT
echo

if [[ $REBOOT =~ ^[Yy]$ ]]
then
  echo "Rebooting now ..."
  execute "reboot now"
fi

echo "done"
