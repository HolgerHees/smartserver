FROM alpine:{{image_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk add --no-cache --update wireguard-tools tzdata

ENTRYPOINT [ "/entrypoint.sh" ]
