FROM openhab/openhab:{{image_version}}-debian

RUN apt-get update && apt-get install iputils-ping

# Speedtest
RUN wget -qO- https://install.speedtest.net/app/cli/ookla-speedtest-{{speedtest_version}}-linux-x86_64.tgz | tar xvz -C /usr/bin/
#RUN apt-get install -y gnupg1 apt-transport-https dirmngr && \
#    curl -s https://install.speedtest.net/app/cli/install.deb.sh | bash && \
#    apt-get install speedtest

COPY init.sh /etc/cont-init.d/
