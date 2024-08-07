FROM alpine:{{alpine_version}}

# Entrypoint
COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk --update --no-cache add bash curl minidlna tini shadow su-exec tzdata

ENTRYPOINT ["/entrypoint.sh"]
#ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
#ENTRYPOINT ["sleep", "500000"]
