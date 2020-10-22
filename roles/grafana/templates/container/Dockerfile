FROM grafana/grafana:{{image_version}}

USER root
RUN sed -i 's/;disable_total_stats.*/disable_total_stats = true/' /etc/grafana/grafana.ini

USER grafana
ENTRYPOINT [ "/run.sh" ]

