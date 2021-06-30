#!/bin/sh

#if ! grep -q "name=\"org.openhab.core.automation.internal.RuleEngineImpl\"" /openhab/userdata/etc/log4j2.xml; then
#    sed -i 's/<\/Loggers>/\n\t\t<Logger level="ERROR" name="org.openhab.core.automation.internal.RuleEngineImpl"\/>\n\t<\/Loggers>/g' /openhab/userdata/etc/log4j2.xml
#fi 
    
#if ! grep -q "name=\"org.openhab.core.automation\"" /openhab/userdata/etc/log4j2.xml; then
#    sed -i 's/<\/Loggers>/\n\t\t<Logger level="DEBUG" name="org.openhab.core.automation"\/>\n\t<\/Loggers>/g' /openhab/userdata/etc/log4j2.xml
#fi 

if ! grep -q "name=\"jsr223.jython\"" /openhab/userdata/etc/log4j2.xml; then
    sed -i 's/<\/Loggers>/\n\t\t<Logger level="DEBUG" name="jsr223.jython"\/>\n\t<\/Loggers>/g' /openhab/userdata/etc/log4j2.xml
fi 
