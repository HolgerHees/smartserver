FROM alpine:{{alpine_version}}

RUN {{alpine_build_cache}} && \
    apk --update add dnsmasq tzdata

ENTRYPOINT ["dnsmasq", "-k"]
