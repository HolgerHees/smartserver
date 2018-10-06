#!/bin/bash

DIRNAME=`dirname "$0"`

RESULT=`${DIRNAME}/TempCmd 2>&1`
CODE=${PIPESTATUS[0]}

#regex="\#([0-9]+).*: +([0-9]+\.[0-9]+)°C"                                                                                                
regex="\#([0-9]+).*\+([0-9]+\.[0-9]+)°C"                                                                                                

IFS=$'\n'

for line in $RESULT
do
	#echo $line
	if [[ $line =~ $regex ]]
	then                                                                                                                   
        sensor=${BASH_REMATCH[1]}                                                                                                                       
        value=${BASH_REMATCH[2]}                                                                                                                       
        #echo $sensor $value                                                                                                                                    
        
        if [ "$sensor" == "1" ]; then
			curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://127.0.0.1:8080/rest/items/Heating_Temperature_Pipe_Out/state"
		elif [ "$sensor" == "2" ]; then
			curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://127.0.0.1:8080/rest/items/Heating_Temperature_Pipe_In/state"
		fi
    fi
done

	#curl -s -X PUT -H "Content-Type: text/plain" -d $value "http://127.0.0.1:8080/rest/items/"$item"/state"
#done
