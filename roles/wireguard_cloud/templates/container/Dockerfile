FROM alpine:{{alpine_version}}

RUN apk add --no-cache --update wireguard-tools
# openssh

# The host keys get regenrated at start of the container
#RUN rm -rf /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_dsa_key

VOLUME /etc/wireguard

EXPOSE {{exposed_port}}/udp
#EXPOSE 22

ENTRYPOINT [ "/etc/wireguard/util/wg-startup.sh" ]
