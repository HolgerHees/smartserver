FROM alpine:{{image_version}} 

COPY entrypoint.sh /entrypoint.sh

RUN apk update && \
    apk upgrade && \
    apk add ca-certificates openssl-dev openssl libffi-dev python3 python3-dev py3-pip py3-yaml gcc musl-dev tzdata openntpd wget && \

# Download and unpack Elastalert.
    wget -O elastalert.zip https://github.com/Yelp/elastalert/archive/{{elastalert_version}}.zip && \
    unzip elastalert.zip && \
    rm elastalert.zip && \
    mv elastalert* "/elastalert" && \
    
# Change working dir.
    cd /elastalert && \

# Install Elastalert.
    python3 setup.py install && \
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
#    rm -rf /elastalert && \
    rm -rf /var/cache/apk/* && \

# Change execute permission
    chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

