FROM alpine:{{image_version}}

COPY entrypoint.sh /usr/sbin/

RUN apk add --no-cache --update wireguard-tools tzdata iptables \
    && chmod +x /usr/sbin/entrypoint.sh

ENTRYPOINT [ "/usr/sbin/entrypoint.sh" ]

EXPOSE {{mobile_vpn_internal_port}}/udp
