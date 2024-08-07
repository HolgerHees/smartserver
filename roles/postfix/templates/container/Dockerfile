FROM alpine:{{alpine_version}}

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk --no-cache add ca-certificates libintl postfix cyrus-sasl-login tzdata git go \
    && mkdir /build \
    && cd /build \
    && git clone https://github.com/kumina/postfix_exporter.git \
    && cd postfix_exporter \
    && go build -tags nosystemd

ENTRYPOINT ["/entrypoint.sh"]
