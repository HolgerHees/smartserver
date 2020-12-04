FROM alpine:{{image_version}}

COPY entrypoint.sh /usr/sbin/

RUN apk add --no-cache --update wireguard-tools \
    && chmod +x /usr/sbin/entrypoint.sh

CMD /usr/sbin/entrypoint.sh

EXPOSE {{mobile_vpn_internal_port}}/udp
