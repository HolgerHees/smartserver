FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk --update --no-cache add python3 py3-pip py3-pexpect py3-requests tzdata git \
#    && pip3 install --break-system-packages --upgrade pip \
    && pip3 install --break-system-packages flask=={{flask_version}} flask-socketio=={{flask_socketio_version}} simple-websocket schedule suntime

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 80/tcp
