FROM alpine:{{image_version}}

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --no-cache add ca-certificates libintl postfix cyrus-sasl-login tzdata git go \
    && mkdir /build \
    && cd /build \
    && git clone https://github.com/kumina/postfix_exporter.git \
    && cd postfix_exporter \
    && go build -tags nosystemd

ENTRYPOINT ["/entrypoint.sh"]
