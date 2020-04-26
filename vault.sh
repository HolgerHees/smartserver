#!/bin/bash

# Search recursively through the current directory for encrypted values
#   - assumes your vault password is in a file vpass

if ! [ -x "$(command -v ansible-vault)" ]; then
  echo 'Error: ansible-vault is not installed.' >&2
  exit 1
fi

ACTION=""
if [ "$1" != "" ]; then
    ACTION="$1"
else
    echo "Usage: vault.sh encrypt|decrypt"
    exit 1
fi

#echo "${VAULTPW}" > /tmp/mypipe &
#ansible-playbook ... --vault-password-file=$vaultpipe

echo -n "Ansible Password: "
read -s PWD
echo ""

vaultpipe=$(mktemp)
echo "${PWD}" > $vaultpipe &

trap "{ rm -f $vaultpipe; }" TERM KILL QUIT INT HUP EXIT

if [ "${ACTION}" = "encrypt" ]; then
  echo -n "Verify Password : "
  read -s PWD_check
  echo ""

  if [ "${PWD}" != "${PWD_check}" ]; then
      echo "password not equal"
      exit;
  fi

  grep -rilL ANSIBLE_VAULT ./config/*/vault/ | grep -v demo | while read N 
  do 
    echo -n "$N • "
    ansible-vault encrypt --vault-password-file $vaultpipe $N
  done
elif [ "${ACTION}" = "decrypt" ]; then
  grep -ril ANSIBLE_VAULT ./config/*/vault/ | grep -v demo | while read N 
  do 
    echo -n "$N • "
    ansible-vault decrypt --vault-password-file $vaultpipe $N
  done
fi
