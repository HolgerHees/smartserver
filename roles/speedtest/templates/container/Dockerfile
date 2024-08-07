FROM e7db/speedtest:{{speedtest_version}}

COPY --chmod=644 ipInfo.js /app/src/ipInfo.js
COPY --chmod=644 ipInfo.js /app/src/gzip.js

COPY --chmod=755 entrypoint.sh /entrypoint.sh

RUN apk --update --no-cache add iperf3

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/entrypoint.sh"]
