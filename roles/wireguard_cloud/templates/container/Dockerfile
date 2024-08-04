FROM alpine:{{image_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk add --no-cache --update wireguard-tools iperf3 tzdata
 
ENTRYPOINT [ "/entrypoint.sh" ]
