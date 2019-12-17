FROM php:7.3-apache

ARG GLOBAL_LOG

#RUN apt-get update

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

#sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf

#RUN apt-get install -y libzip-dev libjpeg62-turbo-dev libpng-dev libfreetype6-dev

RUN docker-php-ext-install mysqli
#RUN docker-php-ext-install exif mbstring zip mysqli pcntl

