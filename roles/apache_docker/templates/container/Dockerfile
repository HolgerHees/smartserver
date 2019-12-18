FROM php:7.3-apache

ARG GLOBAL_LOG

RUN apt-get update

RUN ln -s /etc/apache2/mods-available/auth_digest.load /etc/apache2/mods-enabled/
RUN ln -s /etc/apache2/mods-available/authz_groupfile.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/expires.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/headers.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/lbmethod_bytraffic.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/proxy.conf /etc/apache2/mods-enabled/
RUN ln -s /etc/apache2/mods-available/proxy.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/proxy_html.conf /etc/apache2/mods-enabled/
RUN ln -s /etc/apache2/mods-available/proxy_html.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/proxy_http.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/proxy_balancer.conf /etc/apache2/mods-enabled/
RUN ln -s /etc/apache2/mods-available/proxy_balancer.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/proxy_wstunnel.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/rewrite.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/slotmem_shm.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/socache_shmcb.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/ssl.conf /etc/apache2/mods-enabled/
RUN ln -s /etc/apache2/mods-available/ssl.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/substitute.load /etc/apache2/mods-enabled/

RUN ln -s /etc/apache2/mods-available/xml2enc.load /etc/apache2/mods-enabled/

RUN sed -i "s@ErrorLog.*@ErrorLog $GLOBAL_LOG/error.log@g" /etc/apache2/apache2.conf

RUN sed -i "s/Include ports\.conf/#Include ports\.conf/g" /etc/apache2/apache2.conf

RUN echo 'Include /etc/apache2/_.ansible_vhost-ssl.conf' >> /etc/apache2/apache2.conf

#RUN sed -i 's/maxmemory.*/maxmemory 26gb/' /some/file/some/where.txt

#RUN apt-get install -y libzip-dev libjpeg62-turbo-dev libpng-dev libfreetype6-dev

RUN apt-get install -y libicu-dev zlib1g-dev libzip-dev libjpeg-dev libpng-dev libmagickwand-dev

RUN docker-php-ext-install mysqli pdo_mysql intl zip gd
#RUN docker-php-ext-install exif mbstring zip mysqli pcntl

RUN pecl install apcu-5.1.11
RUN docker-php-ext-enable apcu

RUN pecl install imagick
RUN docker-php-ext-enable imagick

RUN pecl install redis
RUN docker-php-ext-enable redis


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

      
