FROM e7db/speedtest:{{image_version}}

COPY ipInfo.js /app/src/ipInfo.js
COPY ipInfo.js /app/src/gzip.js

RUN chmod 644 /app/src/ipInfo.js && chmod 644 /app/src/gzip.js
