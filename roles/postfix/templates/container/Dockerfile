FROM alpine:{{image_version}}

RUN apk --no-cache add ca-certificates libintl postfix cyrus-sasl-plain cyrus-sasl-login tzdata

COPY entrypoint.sh /usr/sbin/

RUN chmod +x /usr/sbin/entrypoint.sh

ENTRYPOINT ["/usr/sbin/entrypoint.sh"]
