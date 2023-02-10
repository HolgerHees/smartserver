#!/bin/bash

# Search recursively through the current directory for encrypted values
#   - assumes your vault password is in a file vpass

if ! [ -x "$(command -v ansible-vault)" ]; then
  echo 'Error: ansible-vault is not installed.' >&2
  exit 1
fi

ACTION=""
LIMIT=""
for var in "$@"
do
    if [ "$var" == "encrypt" ] || [ "$var" == "decrypt" ]
    then
        ACTION="$var"
    elif [ "$LIMIT" == "" ]
    then
        LIMIT="$var"
    else
        echo "Unknown parameter '$var'"
        echo ""
        ACTION=""
        break
    fi
done

if [ "$ACTION" == "encrypt" ] && [ "$LIMIT" != "" ]
then
    echo "Limit only supported for 'decrypt'"
    echo ""
    ACTION=""
fi

if [ "$ACTION" == "" ]; then
    echo "Usage: vault.sh encrypt"
    echo "       vault.sh decrypt <path_limit>"
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
    if [ "$LIMIT" != "" ] && [[ $N != *"$LIMIT"* ]]
    then
        continue
    fi

    echo -n "$N • "
    ansible-vault decrypt --vault-password-file $vaultpipe $N
  done
fi
