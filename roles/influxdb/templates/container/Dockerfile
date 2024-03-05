FROM influxdb:{{image_version}}-alpine

USER root

RUN apk --no-cache add shadow && \
    groupmod -g {{system_groups['influxdb'].id}} influxdb && \
    usermod -u {{system_users['influxdb'].id}} -g {{system_groups['influxdb'].id}} influxdb && \
    chown -R influxdb:influxdb /home/influxdb && \
    chown -R influxdb:influxdb /var/lib/influxdb2 && \
    chown -R influxdb:influxdb /etc/influxdb2

