FROM alpine:{{alpine_version}}

RUN apk add --no-cache --update wireguard-tools nfs-utils

VOLUME /etc/wireguard

ENTRYPOINT [ "/etc/wireguard/util/wg-startup.sh" ]
