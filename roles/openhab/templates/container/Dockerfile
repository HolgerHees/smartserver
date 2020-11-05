FROM openhab/openhab:{{image_version}}-debian

RUN apt-get update && apt-get install iputils-ping

COPY init.sh /etc/cont-init.d/
