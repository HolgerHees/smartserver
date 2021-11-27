FROM alpine:{{image_version}}

RUN apk add --update samba-common-tools samba-client samba-server

ENTRYPOINT ["smbd", "--foreground", "--debuglevel=1", "--debug-stdout", "--no-process-group"]
