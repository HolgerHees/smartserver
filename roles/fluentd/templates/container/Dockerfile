FROM fluent/fluentd:v{{fluentd_version}}

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends make gcc g++ libc-dev && \
    gem install fluent-plugin-systemd && \
    gem install fluent-plugin-grafana-loki && \
    gem install fluent-plugin-record-modifier && \
    gem install fluent-plugin-rewrite-tag-filter

#RUN buildDeps="sudo make gcc g++ libc-dev" \
# && apt-get update \
# && apt-get install -y --no-install-recommends $buildDeps \
# && sudo gem install fluent-plugin-systemd \
# && sudo gem install fluent-plugin-grafana-loki \
# && sudo gem install fluent-plugin-record-modifier \
# && sudo gem install fluent-plugin-rewrite-tag-filter \
# && sudo gem sources --clear-all \
# && SUDO_FORCE_REMOVE=yes \
#    apt-get purge -y --auto-remove \
#                  -o APT::AutoRemove::RecommendsImportant=false \
#                  $buildDeps \
# && rm -rf /var/lib/apt/lists/* \
# && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

#RUN locale-gen en_US.UTF-8
#ENV LANG en_US.UTF-8

#USER fluent
