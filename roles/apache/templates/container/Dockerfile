FROM httpd:{{apache_version}}

RUN groupadd -g {{system_groups['www'].id}} {{system_groups['www'].name}} && \
    useradd -u {{system_users['www'].id}} -g {{system_groups['www'].id}} -r -s /bin/false {{system_users['www'].name}} && \
    mv /usr/local/apache2/conf/httpd.conf /usr/local/apache2/conf/httpd.conf.bak && \
    apt-get update && \
    apt-get install -y --no-install-recommends apache2-dev libssl-dev libcurl4-openssl-dev libjansson-dev libcjose-dev libpcre2-dev pkg-config certbot git && \
    mkdir /usr/lib/apache2/ && \
    mkdir /usr/lib/apache2/modules && \
    git clone --single-branch --branch v{{openidc_version}} https://github.com/zmartzone/mod_auth_openidc.git && \
    cd mod_auth_openidc/ && \
    ./autogen.sh && \
    autoreconf -fi && \
    ./configure CFLAGS="-g -O0" LDFLAGS="-lrt" && \
    make clean && make test && \
    make -j$(nproc) && \
    cp ./src/.libs/mod_auth_openidc.so /usr/local/apache2/modules/mod_auth_openidc.so
#    && cd / \
#    && rm -rf /mod_auth_openidc \
#    && apt-get purge -y git pkg-config \
#    && apt-get autoremove -y \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*

