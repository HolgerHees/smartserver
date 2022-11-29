FROM alpine:{{image_version}}

COPY entrypoint.sh /usr/sbin/

RUN apk --no-cache add ca-certificates libintl postfix cyrus-sasl-login tzdata git go \
    && mkdir /build \
    && cd /build \
    && git clone https://github.com/kumina/postfix_exporter.git \
    && cd postfix_exporter \
    && go build -tags nosystemd \
    && chmod +x /usr/sbin/entrypoint.sh

ENTRYPOINT ["/usr/sbin/entrypoint.sh"]
