ARG VERSION

FROM alpine:$VERSION

RUN apk --no-cache add dnsmasq

ENTRYPOINT ["dnsmasq", "-k"]
