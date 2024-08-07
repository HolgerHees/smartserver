FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk add --no-cache --update wireguard-tools tzdata

ENTRYPOINT [ "/entrypoint.sh" ]
