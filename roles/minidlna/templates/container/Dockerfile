FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN {{alpine_build_cache}} && \
    apk --update add bash curl minidlna tini shadow su-exec tzdata

ENTRYPOINT ["/entrypoint.sh"]
#ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
#ENTRYPOINT ["sleep", "500000"]
