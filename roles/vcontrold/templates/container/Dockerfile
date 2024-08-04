FROM alpine:{{image_version}}

RUN apk --no-cache add cmake eudev-dev libusb-compat-dev libxml2-dev linux-headers git make gcc musl-dev shadow python3 py3-pip py3-paho-mqtt tzdata inetutils-telnet

#https://medium.com/@gdiener/how-to-build-a-smaller-docker-image-76779e18d48a

RUN groupmod -g {{group_dialout_id.stdout}} dialout && \
    pip3 install --break-system-packages --upgrade pip && \
    pip3 install --break-system-packages pexpect && \
    git clone --single-branch --branch {{vcontrold_version}} https://github.com/openv/vcontrold.git && \
    mkdir vcontrold/build && cd vcontrold/build && cmake -DMANPAGES=OFF -DCMAKE_INSTALL_PREFIX=/usr/ .. && make && make install && \
    cd / && \
    rm -rf /vcontrold

#ENTRYPOINT ["/bin/sleep","3000000"]
#ENTRYPOINT ["/usr/sbin/vcontrold","-n"]
ENTRYPOINT ["/usr/bin/python3","/etc/vcontrold/mqtt.py"]

