ARG VERSION

FROM alpine:$VERSION

RUN apk add --update samba-common-tools samba-client samba-server

ENTRYPOINT ["smbd", "--foreground", "--log-stdout", "--no-process-group"]

