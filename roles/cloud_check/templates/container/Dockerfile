FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add python3 py3-paho-mqtt py3-pip py3-requests py3-tz py3-mysqlclient tzdata && \
    pip3 install --break-system-packages flask=={{flask_version}}

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]
