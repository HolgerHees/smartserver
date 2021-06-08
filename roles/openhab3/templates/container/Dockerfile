FROM openhab/openhab:{{image_version}}-debian

RUN apt-get update && apt-get install iputils-ping

# Speedtest
RUN apt-get install -y gnupg1 apt-transport-https dirmngr && \
    curl -s https://install.speedtest.net/app/cli/install.deb.sh | bash && \
    apt-get install speedtest

COPY init.sh /etc/cont-init.d/
