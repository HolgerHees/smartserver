FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk add --no-cache --update wireguard-tools iperf3 tzdata
 
ENTRYPOINT [ "/entrypoint.sh" ]
