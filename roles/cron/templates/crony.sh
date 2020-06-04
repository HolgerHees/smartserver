#!/bin/bash

set -eu

TMP=$(mktemp -d)
OUT=$TMP/crony.out
ERR=$TMP/crony.err
TRACE=$TMP/crony.trace

IFS='|' read -r name command <<< "$@"
name="$(echo -e "${name}" | sed -e 's/[[:space:]]*$//')"
command="$(echo -e "${command}" | sed -e 's/^[[:space:]]*//')"
#name=`echo "$name" | xargs`
#command=`echo $command | xargs`

#echo "$@";
#echo ":$name:";
#echo ":$command:";
#exit;

set +e
eval "$command" >$OUT 2>$TRACE
RESULT=$?
set -e

PATTERN="^${PS4:0:1}\\+${PS4:1}"
if grep -aq "$PATTERN" $TRACE
then
    ! grep -av "$PATTERN" $TRACE > $ERR
else
    ERR=$TRACE
fi

dt=`date '+%d.%m.%Y %H:%M:%S'`

if [ $RESULT -ne 0 -o -s "$ERR" ]
then
    OUT_VALUE=`cat $OUT`
    ERR_VALUE=`cat $ERR`
    TRACE_VALUE=""
    
    SUBJECT="CRON '$name' ERROR at $dt"
    
    MESSAGE="COMMAND:\n$command"
    MESSAGE+="\n\nCODE\n$RESULT"
    MESSAGE+="\n\nERROR OUTPUT:\n$ERR_VALUE"
    if [ ! -z "$OUT_VALUE" ]
    then
        MESSAGE+="\n\nSTANDARD OUTPUT:\n$OUT_VALUE"
    fi
    
    if [ $TRACE != $ERR ]
    then
        $TRACE_VALUE=`cat $TRACE`
        MESSAGE+="\nTRACE-ERROR OUTPUT:\n$TRACE_VALUE"
    fi
    
    ERR_MSG=`echo $ERR_VALUE | head -c 5000`
    
    JSON=$(jq -c -n --arg job "$name" --arg code "$RESULT" --arg cmd "$command" --arg error_out "$ERR_MSG" '{"job":"\($job)","code":"\($code)","cmd":"\($cmd)","message":"\($error_out)"}');
    echo "$JSON"  | systemd-cat -t crony -p 3

elif [ -s "$OUT" ]
then
    OUT_VALUE=`cat $OUT`

    SUBJECT="CRON '$name' SUCCESS at $dt"

    MESSAGE="COMMAND:\n$command"
    MESSAGE+="\n\nSTANDARD OUTPUT:\n$OUT_VALUE"

    #echo "JOB '$name' was successful" | systemd-cat -t cron -p info
    #echo "send"
    #echo -e "$SUBJECT\n\n$MESSAGE"
else
    MESSAGE=""
fi

if [ ! -z "$MESSAGE" ]
then
    #echo "send"
    #echo -e "$SUBJECT\n\n$MESSAGE"
    
    echo -e "$MESSAGE" | mail -s "$SUBJECT" root
fi

rm -rf "$TMP"
