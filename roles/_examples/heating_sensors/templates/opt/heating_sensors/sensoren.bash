#!/bin/bash

DIRNAME=`dirname "$0"`

RESULT="$(${DIRNAME}/TempCmd 2>&1)"
#CODE=${PIPESTATUS[0]}

#regex="\#([0-9]+).*: +([0-9]+\.[0-9]+)°C"                                                                                                
regex="\#([0-9]+).*\+([0-9]+\.[0-9]+)°C"                                                                                                

IFS=$'\n'

COUNTER=0
for line in $RESULT
do
	if [[ $line =~ $regex ]]
	then                                                                                                                   
        sensor=${BASH_REMATCH[1]}                                                                                                                       
        value=${BASH_REMATCH[2]}                                                                                                                       
        #echo $sensor $value                                                                                                                                    
        
        if [ "$sensor" == "1" ]; then
			curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://openhab:8080/rest/items/pGF_Utilityroom_Heating_Temperature_Pipe_Out/state"
			let COUNTER=COUNTER+1
		elif [ "$sensor" == "2" ]; then
			curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://openhab:8080/rest/items/pGF_Utilityroom_Heating_Temperature_Pipe_In/state"
			let COUNTER=COUNTER+1
		fi
    fi
done

if [[  $COUNTER -lt 2 ]]
then
    echo "Could not read all sensors"
    echo $RESULT
    exit 1
fi

	#curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://openhab:8080/rest/items/"$item"/state"
#done
