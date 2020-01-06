FROM php:7.3-apache

ARG GLOBAL_LOG
ARG WWW_UID
ARG WWW_USERNAME
ARG WWW_GID
ARG WWW_GROUPNAME

RUN groupadd -g $WWW_GID $WWW_GROUPNAME \
  && useradd -u $WWW_UID -g $WWW_GID -r -s /bin/false $WWW_USERNAME \
  && apt-get update \
  && apt-get install -y sudo

# OpenID Connect
RUN apt-get install -y libapache2-mod-auth-openidc
#libapache2-mod-auth-openid

#RUN apt-get install -y libzip-dev libjpeg62-turbo-dev libpng-dev libfreetype6-dev

RUN docker-php-ext-enable opcache \
  && docker-php-ext-install pcntl \
  && docker-php-ext-install exif \
  && docker-php-ext-install mysqli pdo_mysql

# INTL
RUN apt-get install -y libicu-dev \
  && docker-php-ext-install intl

# ZIP
RUN apt-get install -y zlib1g-dev libzip-dev \
  && docker-php-ext-install zip

# APC Cache
RUN pecl install apcu-5.1.11 \
  && docker-php-ext-enable apcu

# ImageMagick
#RUN apt-get install -y libjpeg-dev libpng-dev libmagickwand-dev
RUN apt-get install -y libmagickwand-dev \
  && pecl install imagick \
  && docker-php-ext-enable imagick

# GD Image library with freetype support
RUN apt-get install -y libwebp-dev libjpeg62-turbo-dev libpng-dev libxpm-dev libfreetype6-dev \
  && docker-php-ext-configure gd --with-gd --with-webp-dir --with-jpeg-dir --with-png-dir --with-zlib-dir --with-xpm-dir --with-freetype-dir \
  && docker-php-ext-install gd

# Redis
RUN pecl install redis \
  && docker-php-ext-enable redis

#https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=759209
#  && ln -s /etc/apache2/mods-available/auth_openid.load /etc/apache2/mods-enabled/ \
#  && ln -s /etc/apache2/mods-available/auth_openidc.conf /etc/apache2/mods-enabled/ \
#  && ln -s /etc/apache2/mods-available/auth_openidc.load /etc/apache2/mods-enabled/ \
RUN ln -s /etc/apache2/mods-available/auth_digest.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/authz_groupfile.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/expires.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/headers.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/lbmethod_bytraffic.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_html.conf /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_html.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_http.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_balancer.conf /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_balancer.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/proxy_wstunnel.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/rewrite.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/slotmem_shm.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/socache_shmcb.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/ssl.conf /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/ssl.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/substitute.load /etc/apache2/mods-enabled/ \
  && ln -s /etc/apache2/mods-available/xml2enc.load /etc/apache2/mods-enabled/ \
#  && sed -i "s@LoadModule.*@LoadModule authopenid_module /usr/lib/apache2/modules/mod_auth_openid.so@g" /etc/apache2/mods-available/auth_openid.load \
  && sed -i "s@ErrorLog.*@ErrorLog $GLOBAL_LOG/error.log@g" /etc/apache2/apache2.conf \
  && sed -i "s/Include ports\.conf/#Include ports\.conf/g" /etc/apache2/apache2.conf \
  && echo 'Include /etc/apache2/_.ansible.server.conf' >> /etc/apache2/apache2.conf \
  && echo 'Include /etc/apache2/_.ansible.vhost.d/*.conf' >> /etc/apache2/apache2.conf \
  && mv "/usr/local/etc/php/php.ini-production" "/usr/local/etc/php/php.ini" \
  && sed -i 's/memory_limit.*/memory_limit = 1024M/' /usr/local/etc/php/php.ini

#TODO
#      , systemd-devel         # php-systemd => nextcloud

#MAYBE
#      , php7-devel 
#      , php7-mysql 

#ALREADY ENABLED
#      , php7-mbstring 
#      , php7-posix            # nextcloud
#      , php7-xmlwriter        # nextcloud
#      , php7-xmlreader        # nextcloud
#      , php7-iconv            # nextcloud
#      , php7-dom              # nextcloud
#      , php7-ctype            # nextcloud
#      , php7-json             # phpmyadmin
#      , php7-fileinfo
#      , php7-openssl 
#      , php7-curl 

#DONE
#      , php7-imagick
#      , php7-redis 
#      , php7-gd 
#      , php7-opcache          # nextcloud
#      , php7-APCu             # nextcloud & resize.php
#      , php7-intl             # nextcloud
#      , php7-zip 

      
