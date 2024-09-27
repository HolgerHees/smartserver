#!/bin/sh

if ! grep -q "name=\"jsr223.jython\"" /openhab/userdata/etc/log4j2.xml; then
    sed -i 's/<\/Loggers>/\n\t\t<Logger level="DEBUG" name="jsr223.jython"\/>\n\t<\/Loggers>/g' /openhab/userdata/etc/log4j2.xml
fi 

if ! grep -q "name=\"org.eclipse.jetty.util.ssl.SslContextFactory.config\"" /openhab/userdata/etc/log4j2.xml; then
    # needed to hide warning about "Weak cipher suite" in samsung tv binding
    # https://github.com/openhab/openhab-addons/issues/17273
    # https://community.openhab.org/t/weak-cipher-suite-warnings/157840
    sed -i 's/<\/Loggers>/\n\t\t<Logger level="ERROR" name="org.eclipse.jetty.util.ssl.SslContextFactory.config"\/>\n\t<\/Loggers>/g' /openhab/userdata/etc/log4j2.xml
fi
