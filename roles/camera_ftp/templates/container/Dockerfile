FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add procps vsftpd tzdata

ENTRYPOINT [ "/entrypoint.sh" ]
 
