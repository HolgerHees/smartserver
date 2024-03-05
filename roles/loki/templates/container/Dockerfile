FROM grafana/loki:{{image_version}}

USER root

RUN apk --no-cache add shadow && \
    groupmod -g {{system_groups['loki'].id}} loki && \
    usermod -u {{system_users['loki'].id}} -g {{system_groups['loki'].id}} loki && \
    chown -R loki:loki /etc/loki && \
    chown -R loki:loki /loki

