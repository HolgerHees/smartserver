FROM php:{{image_version}}-fpm

RUN groupadd -g {{system_groups['www'].id}} {{system_groups['www'].name}} && \
  useradd -u {{system_users['www'].id}} -g {{system_groups['www'].id}} -r -s /bin/false {{system_users['www'].name}} && \
  apt-get update && \
  apt-get install -y sudo && \

  docker-php-ext-enable opcache && \
  docker-php-ext-install pcntl && \
  docker-php-ext-install exif && \
  docker-php-ext-install bcmath && \
  docker-php-ext-install mysqli pdo_mysql && \

# GMP => needed by nextcloud bookmarks
#RUN apt-get install -y libgmp-dev re2c libmhash-dev libmcrypt-dev file \
#  && ln -s /usr/include/x86_64-linux-gnu/gmp.h /usr/local/include/ \
#  && docker-php-ext-configure gmp \
#  && docker-php-ext-install gmp
  apt-get install -y libgmp-dev && \
  docker-php-ext-install gmp && \
  
# INTL
  apt-get install -y libicu-dev && \
  docker-php-ext-install intl && \

# ZIP
  apt-get install -y zlib1g-dev libzip-dev && \
  docker-php-ext-install zip && \

# APC Cache
  pecl install apcu-5.1.18 && \
  docker-php-ext-enable apcu && \

# ImageMagick
#RUN apt-get install -y libjpeg-dev libpng-dev libmagickwand-dev
  apt-get install -y libmagickwand-dev && \
  pecl install imagick && \
  docker-php-ext-enable imagick && \

# GD Image library with freetype support
  apt-get install -y libwebp-dev libjpeg62-turbo-dev libpng-dev libxpm-dev libfreetype6-dev && \
  docker-php-ext-configure gd --enable-gd --with-webp --with-jpeg --with-xpm --with-freetype && \
  docker-php-ext-install gd && \

# Redis
  pecl install redis && \
  docker-php-ext-enable redis && \
  
# CLEANUPS
  apt-get autoremove -y && \
  apt-get clean && \
  
  mv "/usr/local/etc/php/php.ini-production" "/usr/local/etc/php/php.ini" && \
  sed -i 's/memory_limit.*/memory_limit = 1024M/' /usr/local/etc/php/php.ini && \
  sed -i 's/pm.start_servers.*/pm.start_servers = 15/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/pm.max_children.*/pm.max_children = 100/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/pm.min_spare_servers.*/pm.min_spare_servers = 15/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/pm.max_spare_servers.*/pm.max_spare_servers = 30/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/pm.process_idle_timeout.*/pm.process_idle_timeout = 15s/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/pm.max_requests.*/pm.max_requests = 500/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/access.log.*/access.log = \/dev\/null/' /usr/local/etc/php-fpm.d/docker.conf





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

      
