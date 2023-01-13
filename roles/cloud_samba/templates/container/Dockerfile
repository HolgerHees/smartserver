FROM alpine:{{image_version}}

RUN apk add --no-cache --update samba-common-tools samba-client samba-server tzdata

ENTRYPOINT [ "/etc/cloud_samba/util/startup.sh" ]

EXPOSE 445/tcp
