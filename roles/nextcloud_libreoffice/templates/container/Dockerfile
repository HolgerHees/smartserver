FROM onlyoffice/documentserver:{{libreoffice_version}}

RUN sed -i 's/APT::Periodic::Update-Package-Lists.*/APT::Periodic::Update-Package-Lists "0";/' /etc/apt/apt.conf.d/10periodic && \
    sed -i 's/APT::Periodic::Update-Package-Lists.*/APT::Periodic::Update-Package-Lists "0";/' /etc/apt/apt.conf.d/20auto-upgrades && \
    sed -i 's/APT::Periodic::Unattended-Upgrade.*/APT::Periodic::Unattended-Upgrade "0";/' /etc/apt/apt.conf.d/20auto-upgrades && \
    dpkg-reconfigure unattended-upgrades

ENTRYPOINT [ "/bin/sh", "-c", "/app/ds/run-document-server.sh" ]

