#!/bin/sh

if ! grep -q "log4j2.logger.jsr223Script" /openhab/userdata/etc/org.ops4j.pax.logging.cfg; then
    echo "log4j2.logger.jsr223Script.name = jsr223.jython" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
    echo "log4j2.logger.jsr223Script.level = DEBUG" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
    echo "log4j2.logger.jsr223Default.name = org.openhab.core.automation" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
    echo "log4j2.logger.jsr223Default.level = DEBUG" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
    echo "log4j2.logger.jsr223Trigger.name = org.openhab.core.automation.internal.RuleEngineImpl" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
    echo "log4j2.logger.jsr223Trigger.level = ERROR" >> /openhab/userdata/etc/org.ops4j.pax.logging.cfg
fi 

mkdir -p /openhab/userdata/config/org/openhab/

ln -sf /openhab/conf/habpanel.config /openhab/userdata/config/org/openhab/habpanel.config

chown -R openhab:openhab /openhab/userdata/
