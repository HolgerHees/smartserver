FROM alpine:{{image_version}}

COPY entrypoint.sh /usr/sbin/

RUN apk --no-cache add ca-certificates libintl postfix cyrus-sasl-login tzdata \
    && chmod +x /usr/sbin/entrypoint.sh

ENTRYPOINT ["/usr/sbin/entrypoint.sh"]
