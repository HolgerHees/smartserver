FROM alpine:{{image_version}}

RUN apk --no-cache add dnsmasq tzdata
#RUN apk --no-cache add dnsmasq-dnssec

ENTRYPOINT ["dnsmasq", "-k"]
