FROM alpine:{{image_version}}

RUN apk add --no-cache --update wireguard-tools

ENTRYPOINT [ "/etc/wireguard/util/wg-startup.sh" ]

EXPOSE {{vault_wireguard_mobile_internal_port}}/udp
