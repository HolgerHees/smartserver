FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add shadow git python3 py3-pip py3-pyserial && \
    pip3 install --break-system-packages paho-mqtt && \
    groupmod -g {{group_dialout_id.stdout}} dialout

#ENTRYPOINT ["/bin/sleep","3000000"]
#to see podman logs -f python must run 'unbuffered'
#https://stackoverflow.com/questions/51362213/docker-compose-not-printing-stdout-in-python-app
ENTRYPOINT ["/entrypoint.sh"]
