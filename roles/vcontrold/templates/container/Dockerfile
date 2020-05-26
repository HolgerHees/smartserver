#FROM alpine:{{alpine_version}}

#RUN apk --no-cache add cmake eudev-dev libusb-compat-dev libxml2-dev linux-headers git make gcc musl-dev

FROM debian:{{debian_version}}

RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y libxml2-dev cmake git && \
    git clone --single-branch --branch {{vcontrold_version}} https://github.com/openv/vcontrold.git && \
    mkdir vcontrold/build && cd vcontrold/build && cmake -DMANPAGES=OFF -DCMAKE_INSTALL_PREFIX=/usr/ .. && make && make install && \
    cd / && \
    rm -rf /vcontrold && \
    apt-get purge -y --auto-remove cmake git

ENTRYPOINT ["/usr/sbin/vcontrold","-n"]
