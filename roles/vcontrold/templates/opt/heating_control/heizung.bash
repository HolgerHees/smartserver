#!/bin/bash
DIRNAME=`dirname "$0"`

RESULT=`docker exec -i vcontrold sh -c "/usr/bin/vclient -h 127.0.0.1 -p 3002 -f ${DIRNAME}/heizung.cmd -t ${DIRNAME}/heizung.tpl 2>&1"`
CODE=${PIPESTATUS[0]}

hasError=0
while IFS='|' read -r item value status; do
    if [ -z "$value" ] || [ -z "$status" ] || [[ ${status:0:2} != "OK" ]]; then
        hasError=1
    else
        #echo $item
        curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://127.0.0.1:8080/rest/items/"$item"/state"
    fi
done <<< "$RESULT"

if [ "$hasError" -eq 1 ]; then
    printf "STATUS: %s\nRESULT: %s" "$CODE" "$RESULT" > "{{global_log}}/heizung/Heizungsdatenfehler_$(date +"%d.%m.%Y_%H:%M:%S")"
fi
