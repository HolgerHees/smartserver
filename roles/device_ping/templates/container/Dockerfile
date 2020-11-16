FROM alpine:{{alpine_version}}

RUN apk update && apk upgrade &&  apk --update --no-cache add python3 py3-paho-mqtt coreutils tcpdump arping

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/usr/bin/python3","/etc/device_ping/mqtt.py"]

