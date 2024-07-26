FROM alpine:{{alpine_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --update --no-cache add python3 py3-pip py3-paho-mqtt py3-websocket-client coreutils tcpdump arping arp-scan fping nmap nmap-scripts{{ ' iptables ip6tables iptables-legacy' if not nftables_enabled else ' nftables' }} wireguard-tools-wg-quick tzdata \
    && pip3 install --break-system-packages --upgrade pip \
    && pip3 install --break-system-packages flask=={{flask_version}} flask-socketio=={{flask_socketio_version}} simple-websocket fritzconnection netflow schedule \
    && mkdir /build \
    && cd /build \
    && wget -qO- https://install.speedtest.net/app/cli/ookla-speedtest-{{speedtest_version}}-linux-x86_64.tgz | tar xvz -C /build

#    && apk --update --no-cache add git autoconf automake make gcc g++ libpcap-dev \
#    && git clone https://github.com/royhills/arp-scan.git \
#    && cd /build/arp-scan/ \
#    && autoreconf --install \
#    && ./configure \
#    && make \
#    && make install \
#    && cd /build \

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]

