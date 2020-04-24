ARG VERSION

FROM alpine:$VERSION

RUN apk add --no-cache --update wireguard-tools
# openssh

# The host keys get regenrated at start of the container
#RUN rm -rf /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_dsa_key

RUN mkdir /etc/wireguard/util
COPY wg-startup.sh /etc/wireguard/util/wg-startup.sh

RUN chmod 700 /etc/wireguard/util/wg-startup.sh
RUN mkdir /etc/wireguard/config

VOLUME /etc/wireguard/config

EXPOSE 51820/udp
#EXPOSE 22

ENTRYPOINT [ "/etc/wireguard/util/wg-startup.sh" ]
