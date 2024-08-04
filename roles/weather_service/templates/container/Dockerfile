FROM alpine:{{image_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --update --no-cache add python3 py3-pip py3-paho-mqtt py3-requests py3-tz py3-mysqlclient tzdata \
    && pip3 install --break-system-packages --upgrade pip \
    && pip3 install --break-system-packages flask=={{flask_version}} flask-socketio=={{flask_socketio_version}} simple-websocket schedule suntime

#ENTRYPOINT ["/bin/sleep","3000000"]
#ENTRYPOINT ["/usr/bin/python3","/etc/weather_service/daemon.py"]
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 80/tcp
