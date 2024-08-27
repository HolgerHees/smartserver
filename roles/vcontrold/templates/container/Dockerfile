FROM alpine:{{alpine_version}}

RUN {{alpine_build_cache}} && \
    apk --update add cmake eudev-dev libusb-compat-dev libxml2-dev linux-headers git make gcc musl-dev shadow python3 py3-pip py3-paho-mqtt tzdata inetutils-telnet && \
    groupmod -g {{group_dialout_id.stdout}} dialout && \
    pip3 install --break-system-packages pexpect && \
    git clone --single-branch --branch {{vcontrold_version}} https://github.com/openv/vcontrold.git && \
    mkdir vcontrold/build && \
    cd vcontrold/build && \
    cmake -DMANPAGES=OFF -DCMAKE_INSTALL_PREFIX=/usr/ .. && \
    make && \
    make install

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/usr/bin/python3","/etc/vcontrold/mqtt.py"]

