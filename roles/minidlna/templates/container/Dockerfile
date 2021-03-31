FROM alpine:{{alpine_version}}

# Install
RUN apk --no-cache add bash curl minidlna tini shadow su-exec

# Entrypoint
COPY entrypoint.sh /

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
#ENTRYPOINT ["sleep", "500000"]
