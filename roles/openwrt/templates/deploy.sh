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
    echo "Execute '$COMMAND'"
    sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$SSHHOST $COMMAND
    RETCODE=$?
  elif [ "$SSHAUTH" == "publickey" ]
  then
    echo "Execute '$COMMAND'"
    ssh $SSHHOST $COMMAND
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
    COMMAND="scp -rp $SOURCE/$IP/* root@$SSHHOST:/"
    echo "Execute " $COMMAND
    sshpass -f <(printf '%s\n' $PASSWORD) $COMMAND
  elif [ "$SSHAUTH" == "publickey" ]
  then
    COMMAND="scp -rp $SOURCE/$IP/* $SSHHOST:/"
    echo "Execute " $COMMAND
    $COMMAND
  fi

  unset COMMAND
}

authenticate() {

  echo -n "Check auth type ... "
  if ssh-keygen -F "$HOSTNAME" > /dev/null; then
      export SSHHOST="$HOSTNAME"
  else
      export SSHHOST="$IP"
  fi

  ssh -o PubkeyAuthentication=yes -o PasswordAuthentication=no -o ChallengeResponseAuthentication=no $SSHHOST /bin/true 2> /dev/null
  EXIT_CODE=`echo $?`

  if [ "$EXIT_CODE" -eq 6 ]
  then
    echo "Unknown key fingerprint."
    echo "Login manually first"
    exit
  elif [ "$EXIT_CODE" -eq 0 ]
  then
    echo "publickey"
    export SSHAUTH="publickey"
  else
    echo "password"
    export SSHHOST="$IP"
    export SSHAUTH="password"

    N=5
    for i in $(seq 1 $N); do
      read -p "Enter password: " -s PASSWORD
      echo

      echo -n "Check authentication ... "
      execute "/bin/true"

      EXIT_CODE=`echo $?`

      if [ "$EXIT_CODE" -eq 0 ]
      then
        echo "Authentication ok"
        break
      else
        unset PASSWORD
      fi
    done

    if test -z "$PASSWORD"
    then
      echo "Exit... Got no valid password after $N retries."
      exit
    fi
  fi
}

connectivity() {
  N=5
  for i in $(seq 1 $N); do
    if [ -z "$IP" ]
    then
      read -p "Enter IP adress: " IP
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

read -p "Reboot now? [y/N]: " REBOOT
echo

if [[ $REBOOT =~ ^[Yy]$ ]]
then
  echo "Rebooting now ..."
  execute "reboot now"
fi

echo "done"
