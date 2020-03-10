ARG VERSION

FROM amazon/opendistro-for-elasticsearch-kibana:$VERSION

COPY kibana.yml /usr/share/kibana/config/kibana.yml

RUN /usr/share/kibana/bin/kibana-plugin remove opendistro_security
