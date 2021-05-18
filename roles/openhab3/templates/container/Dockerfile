FROM openhab/openhab:{{image_version}}-debian

RUN apt-get update && apt-get install iputils-ping

# Speedtest
RUN apt-get install -y gnupg1 apt-transport-https dirmngr && \
    export INSTALL_KEY=379CE192D401AB61 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys $INSTALL_KEY && \
    echo "deb https://ookla.bintray.com/debian generic main" | tee  /etc/apt/sources.list.d/speedtest.list && \
    apt-get update && \
    apt-get install -y speedtest

# sudo apt-get remove speedtest-cli

COPY init.sh /etc/cont-init.d/
