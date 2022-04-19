#!/bin/bash
 
authenticate() {
  N=5
  for i in $(seq 1 $N); do
    if [ -z "$PASSWORD" ]
    then
      echo -n "Enter password": 
      read -s PASSWORD
      echo
    fi
    
    echo -n "Check password ... "
    sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP /bin/true
    if [ $? -eq 0 ]
    then
      echo "ok"
      break
    else
      unset PASSWORD
    fi
  done
  
  if [ -z "$PASSWORD" ]
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

SOURCE=`dirname "$0"`

connectivity

authenticate

echo "Installing software ..."
sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "opkg update"
sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "opkg remove wpad-basic-wolfssl"
sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "opkg install mc wpad-wolfssl hostapd-utils snmpd"

echo "Copy default configs ..."
sshpass -f <(printf '%s\n' $PASSWORD) scp -r $SOURCE/default/* root@$IP:/

# must be last because of changed shadow
echo "Copy custom configs ..."
sshpass -f <(printf '%s\n' $PASSWORD) scp -r $SOURCE/$IP/* root@$IP:/

authenticate

#/etc/init.d/rpcd restart
#/etc/init.d/snmpd restart

echo -n "Reboot now? [y/N]": 
read REBOOT
echo

if [[ $REBOOT =~ ^[Yy]$ ]]
then
  echo "Rebooting now ..."
  sshpass -f <(printf '%s\n' $PASSWORD) ssh root@$IP "reboot now"
fi

echo "done"
