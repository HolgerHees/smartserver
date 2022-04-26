FROM librenms/librenms:{{image_version}}

COPY AuthorizerBase.php /opt/librenms/LibreNMS/Authentication/AuthorizerBase.php

RUN chmod 644 /opt/librenms/LibreNMS/Authentication/AuthorizerBase.php && \
    chown nobody:nogroup /opt/librenms/LibreNMS/Authentication/AuthorizerBase.php
