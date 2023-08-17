FROM alpine:{{alpine_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --update --no-cache add python3 py3-inotify py3-paho-mqtt py3-pip coreutils tcpdump arping fping nmap nmap-scripts iptables wireguard-tools-wg-quick tzdata \
    && pip3 install --upgrade pip \
    && pip3 install flask flask-socketio==5.2.0 simple-websocket fritzconnection netflow schedule \
    && apk --update --no-cache add git autoconf automake make gcc g++ libpcap-dev \
    && mkdir /build \
    && cd /build \
    && git clone https://github.com/royhills/arp-scan.git \
    && cd /build/arp-scan/ \
    && autoreconf --install \
    && ./configure \
    && make \
    && make install \
    && cd /build \
    && wget -qO- https://install.speedtest.net/app/cli/ookla-speedtest-{{speedtest_version}}-linux-x86_64.tgz | tar xvz -C /build

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]

