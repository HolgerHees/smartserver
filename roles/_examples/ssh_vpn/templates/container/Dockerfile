FROM alpine:{{image_version}}

EXPOSE {{vault_ssh_vpn_internal_port}}
#COPY rootfs /

RUN apk add --no-cache openssh python2 python3

ENTRYPOINT [ "/etc/ssh/util/entrypoint.sh" ]
#CMD [ "/bin/sleep","5000" ]
