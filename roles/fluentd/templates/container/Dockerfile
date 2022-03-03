FROM fluent/fluentd:v{{image_version}}

USER root

COPY out_loki.rb /out_loki.rb

RUN buildDeps="sudo make gcc g++ libc-dev" \
 && apt-get update \
 && apt-get install -y --no-install-recommends $buildDeps \
 && sudo gem install fluent-plugin-systemd \
 && sudo gem install fluent-plugin-grafana-loki \
 && sudo gem install fluent-plugin-record-modifier \
 && sudo gem install fluent-plugin-rewrite-tag-filter \
 && sudo gem sources --clear-all \
 && SUDO_FORCE_REMOVE=yes \
    apt-get purge -y --auto-remove \
                  -o APT::AutoRemove::RecommendsImportant=false \
                  $buildDeps \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem \
 && path="$(gem which 'fluent/plugin/out_loki.rb' | grep '{{grafana_loki_version}}')" \
 && mv /out_loki.rb $path || (echo 'wrong grafana-loki plugin version' && exit 1)
 
#RUN locale-gen en_US.UTF-8
#ENV LANG en_US.UTF-8

#USER fluent
