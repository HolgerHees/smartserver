FROM amazon/opendistro-for-elasticsearch-kibana:1.4.0

COPY kibana.yml /usr/share/kibana/config/kibana.yml

RUN /usr/share/kibana/bin/kibana-plugin remove opendistro_security
