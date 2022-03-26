FROM grafana/grafana:{{image_version}}

USER root
RUN sed -i '/\[auth.proxy\].*/a enabled = true' /etc/grafana/grafana.ini && \
    sed -i 's/;allowed_origins.*/allowed_origins = */' /etc/grafana/grafana.ini && \
    sed -i 's/;reporting_enabled.*/reporting_enabled = false/' /etc/grafana/grafana.ini && \
    sed -i 's/;check_for_updates.*/check_for_updates = false/' /etc/grafana/grafana.ini && \
    sed -i 's/;disable_gravatar.*/disable_gravatar = true/' /etc/grafana/grafana.ini

USER grafana
ENTRYPOINT [ "/run.sh" ]

