FROM e7db/speedtest:{{image_version}}

COPY ipInfo.js /app/src/ipInfo.js
COPY ipInfo.js /app/src/gzip.js

RUN chmod 644 /app/src/ipInfo.js && chmod 644 /app/src/gzip.js

COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && apk --update --no-cache add iperf3

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]
