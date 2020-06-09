FROM alpine:{{image_version}} 

RUN apk update && \
    apk upgrade && \
    apk add ca-certificates openssl-dev openssl libffi-dev python3 python3-dev py3-pip py3-yaml gcc musl-dev tzdata openntpd wget && \
# Download and unpack Elastalert.
    wget -O elastalert.zip https://github.com/Yelp/elastalert/archive/{{elastalert_version}}.zip && \
    unzip elastalert.zip && \
    rm elastalert.zip && \
    mv elastalert* "/elastalert"

WORKDIR "/elastalert"

# Install Elastalert.
RUN python3 setup.py install && \
    pip install -e . && \
    pip uninstall twilio --yes && \
    pip install twilio==6.0.0 && \

# Install Supervisor.
#    easy_install supervisor && \

# Create directories. The /var/empty directory is used by openntpd.
    mkdir -p /etc/elastalert && \
    mkdir -p /var/empty && \

# Clean up.
    apk del python3-dev && \
    apk del musl-dev && \
    apk del gcc && \
    apk del openssl-dev && \
    apk del libffi-dev && \
    rm -rf /var/cache/apk/*
    
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

# Copy the script used to launch the Elastalert when a container is started.
#COPY ./start-elastalert.sh /opt/
# Make the start-script executable.
#RUN chmod +x /opt/start-elastalert.sh

# Define mount points.
#VOLUME [ "${CONFIG_DIR}", "${RULES_DIRECTORY}", "${LOG_DIR}"]

# Launch Elastalert when a container is started.
#CMD ["/opt/start-elastalert.sh"]
