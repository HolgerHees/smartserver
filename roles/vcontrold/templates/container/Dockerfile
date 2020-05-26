FROM alpine:{{alpine_version}}

RUN apk --no-cache add cmake eudev-dev libusb-compat-dev libxml2-dev linux-headers git make gcc musl-dev

RUN git clone --single-branch --branch {{vcontrold_version}} https://github.com/openv/vcontrold.git 

RUN mkdir vcontrold/build && cd vcontrold/build && cmake -DMANPAGES=OFF -DCMAKE_INSTALL_PREFIX=/usr/ .. && make && make install

ENTRYPOINT ["/bin/sleep","30000000000"]
