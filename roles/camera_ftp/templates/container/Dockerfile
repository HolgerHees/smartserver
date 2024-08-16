FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk --update --no-cache add procps vsftpd tzdata

ENTRYPOINT [ "/entrypoint.sh" ]
 
