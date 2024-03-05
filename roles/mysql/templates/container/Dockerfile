FROM mariadb:{{image_version}}

USER root

RUN groupmod -g {{system_groups['mysql'].id}} mysql && \
    usermod -u {{system_users['mysql'].id}} -g {{system_groups['mysql'].id}} mysql && \
    chown -R mysql:mysql /var/lib/mysql /run/mysqld

