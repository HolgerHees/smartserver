FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add python3 py3-pip py3-pexpect py3-requests tzdata util-linux-misc && \
    pip3 install --break-system-packages flask=={{flask_version}} flask-socketio=={{flask_socketio_version}} simple-websocket redis

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]
