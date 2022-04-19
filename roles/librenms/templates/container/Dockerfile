FROM librenms/librenms:{{image_version}}

COPY HttpAuthAuthorizer.php /opt/librenms/LibreNMS/Authentication/HttpAuthAuthorizer.php

RUN chmod 644 /opt/librenms/LibreNMS/Authentication/HttpAuthAuthorizer.php && \
    chown nobody:nogroup /opt/librenms/LibreNMS/Authentication/HttpAuthAuthorizer.php
