FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add python3 py3-pip py3-paho-mqtt py3-websocket-client coreutils tcpdump arping arp-scan fping nmap nmap-scripts nftables wireguard-tools-wg-quick tzdata && \
    pip3 install --break-system-packages flask=={{flask_version}} flask-socketio=={{flask_socketio_version}} simple-websocket fritzconnection netflow schedule && \
    mkdir /build && \
    cd /build && \
    wget -qO- https://install.speedtest.net/app/cli/ookla-speedtest-{{speedtest_version}}-linux-{{ansible_architecture}}.tgz | tar xvz -C /build

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]

