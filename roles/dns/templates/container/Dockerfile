FROM alpine:{{image_version}}

RUN apk --no-cache add dnsmasq

ENTRYPOINT ["dnsmasq", "-k"]
