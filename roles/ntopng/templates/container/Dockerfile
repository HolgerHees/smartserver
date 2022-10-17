FROM alpine:{{alpine_version}}

ENV WORKDIR /ntop.build
WORKDIR ${WORKDIR}

RUN apk --no-cache add \
    git bash shadow su-exec \
    autoconf automake make gcc g++ libtool pkgconfig  \
    libpcap-dev \
    zeromq-dev json-c-dev openssl-dev curl-dev libmaxminddb-dev sqlite-dev mariadb-connector-c-dev \
    musl-dev linux-headers rrdtool-dev \
    go

RUN cd ${WORKDIR} && git clone --branch {{ndpi_version}}-stable https://github.com/ntop/nDPI.git nDPI && \
    cd nDPI && ./autogen.sh --with-only-libndpi && ./configure && make -j8

RUN cd ${WORKDIR} && git clone --branch {{ntopng_version}}-stable https://github.com/ntop/ntopng.git ntopng && \
    cd ntopng && ./autogen.sh && ./configure && make -j8

RUN cd ${WORKDIR} && git clone https://github.com/synfinatic/netflow2ng netflow2ng && \
    cd netflow2ng && make -B

RUN mkdir /ntop && cd ${WORKDIR} && \
    mv ./netflow2ng/dist/netflow2ng* /ntop/netflow2ng && \
    chmod +x /ntop/netflow2ng && \
    mv ./ntopng/httpdocs /ntop/ && \
    mv ./ntopng/ntopng /ntop/ && \
    mv ./ntopng/third-party /ntop/ && \
    mv ./ntopng/scripts /ntop/ && \
    mv ./ntopng/doc /ntop/

# rm -r ${WORKDIR}

CMD ["sleep", "infinity"]

EXPOSE 3000/tcp
EXPOSE 2055/udp

