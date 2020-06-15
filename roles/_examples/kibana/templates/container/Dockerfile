FROM amazon/opendistro-for-elasticsearch-kibana:{{image_version}}

COPY kibana.yml /usr/share/kibana/config/kibana.yml

RUN /usr/share/kibana/bin/kibana-plugin remove opendistro_security
