FROM alpine:{{image_version}}

# Entrypoint
COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --update --no-cache add bash curl minidlna tini shadow su-exec tzdata

ENTRYPOINT ["/entrypoint.sh"]
#ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
#ENTRYPOINT ["sleep", "500000"]
