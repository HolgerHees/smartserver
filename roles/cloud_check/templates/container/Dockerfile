FROM alpine:{{alpine_version}}

RUN apk --update --no-cache add python3 py3-paho-mqtt py3-pip py3-requests py3-tz py3-mysqlclient tzdata \
    && pip3 install --break-system-packages --upgrade pip \
    && pip3 install --break-system-packages flask=={{flask_version}}

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/usr/bin/python3","/etc/cloud_check/daemon.py"]

EXPOSE 80/tcp
