FROM alpine:{{image_version}}

RUN apk add --no-cache --update samba-common-tools samba-client samba-server cifs-utils tzdata

ENTRYPOINT [ "/etc/samba/util/startup.sh" ]

EXPOSE 445/tcp
