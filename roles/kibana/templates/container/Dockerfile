FROM amazon/opendistro-for-elasticsearch-kibana:1.2.1

COPY kibana.yml /usr/share/kibana/config/kibana.yml

RUN /usr/share/kibana/bin/kibana-plugin remove opendistro_security
