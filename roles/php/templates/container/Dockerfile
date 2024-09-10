FROM php:{{php_version}}-fpm

RUN apt-get update && \
  apt-get install -y sudo \
# preview generator nextcloud
  ffmpeg \
# GMP => needed by nextcloud bookmarks
  libgmp-dev \
# INTL
  libicu-dev \
# ZIP
  zlib1g-dev libzip-dev \
# ImageMagick
  libmagickwand-dev git \
# GD Image library with freetype support
  libwebp-dev libjpeg62-turbo-dev libpng-dev libxpm-dev libfreetype6-dev && \


  docker-php-ext-enable opcache && \
  docker-php-ext-install -j$(nproc) pcntl && \
  docker-php-ext-install -j$(nproc) exif && \
  docker-php-ext-install -j$(nproc) bcmath && \
  docker-php-ext-install -j$(nproc) mysqli pdo_mysql && \
  docker-php-ext-install -j$(nproc) sysvsem && \

# GMP => needed by nextcloud bookmarks
  docker-php-ext-install -j$(nproc) gmp && \
  
# INTL
  docker-php-ext-install -j$(nproc) intl && \

# ZIP
  docker-php-ext-install -j$(nproc) zip && \

# APC Cache
  pecl install apcu && \
  docker-php-ext-enable apcu && \

# ImageMagick
# pecl install imagick
#    https://github.com/Imagick/imagick/issues/640
#    https://github.com/Imagick/imagick/pull/641
#    28f27044e435a2b203e32675e942eb8de620ee58 => 10.09.2024
  cd /tmp && \
  git clone https://github.com/Imagick/imagick.git && \
  cd /tmp/imagick && \
  git checkout 28f27044e435a2b203e32675e942eb8de620ee58 && \
  pecl install /tmp/imagick/package.xml && \
  docker-php-ext-enable imagick && \

# GD Image library with freetype support
  docker-php-ext-configure gd --enable-gd --with-webp --with-jpeg --with-xpm --with-freetype && \
  docker-php-ext-install -j$(nproc) gd && \

# Redis
  pecl install redis && \
  docker-php-ext-enable redis && \
  
# CLEANUPS
#  apt-get autoremove -y && \
#  apt-get clean && \
  
  mv "/usr/local/etc/php/php.ini-production" "/usr/local/etc/php/php.ini" && \
  echo "apc.enable_cli=1\n" >> "/usr/local/etc/php/conf.d/docker-php-ext-apcu.ini" && \
  
  echo "opcache.jit_buffer_size = 100M\n" >> "/usr/local/etc/php/conf.d/docker-php-ext-opcache.ini" && \
  echo "opcache.jit = 1205\n" >> "/usr/local/etc/php/conf.d/docker-php-ext-opcache.ini" && \
  # https://github.com/php/php-src/issues/7817
  #echo "opcache.jit = 1255\n" >> "/usr/local/etc/php/conf.d/docker-php-ext-opcache.ini" && \
  # interned_strings_buffer was running full
  echo "opcache.interned_strings_buffer = 16\n" >> "/usr/local/etc/php/conf.d/docker-php-ext-opcache.ini" && \
  
  sed -i 's/^[;]*memory_limit.*$/memory_limit = 1024M/' /usr/local/etc/php/php.ini && \
  sed -i 's/^[;]*upload_max_filesize.*$/upload_max_filesize = 2048M/' /usr/local/etc/php/php.ini && \
  sed -i 's/^[;]*post_max_size.*$/post_max_size = 2048M/' /usr/local/etc/php/php.ini && \
  sed -i 's/^[;]*max_execution_time.*$/max_execution_time = 600/' /usr/local/etc/php/php.ini && \
  sed -i 's/^[;]*expose_php.*$/expose_php = Off/' /usr/local/etc/php/php.ini && \

  sed -i 's/^[;]*pm[^\.]*$/pm = dynamic/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.start_servers.*$/pm.start_servers = 8/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.min_spare_servers.*$/pm.min_spare_servers = 8/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.max_spare_servers.*$/pm.max_spare_servers = 16/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.process_idle_timeout.*$/pm.process_idle_timeout = 15s/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.max_children.*$/pm.max_children = 200/' /usr/local/etc/php-fpm.d/www.conf && \
  sed -i 's/^[;]*pm.max_requests.*$/pm.max_requests = 500/' /usr/local/etc/php-fpm.d/www.conf && \

  sed -i 's/access.log.*/access.log = \/dev\/null/' /usr/local/etc/php-fpm.d/docker.conf && \
  sed -i 's/domain="coder" rights="none"/domain="coder" rights="read"/' /etc/ImageMagick-6/policy.xml

#  sed -i 's/error_log.*/error_log = \/dev\/null/' /usr/local/etc/php-fpm.d/docker.conf
#  sed -i '1 a /bin/ln -sf /proc/$$/fd/2 /tmp/stderr' /usr/local/bin/docker-php-entrypoint

# https://stitcher.io/blog/php-8-jit-setup

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

      
