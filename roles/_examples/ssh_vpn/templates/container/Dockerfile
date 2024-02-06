FROM alpine:{{image_version}}

EXPOSE {{ssh_vpn_internal_port}}
#COPY rootfs /

RUN apk add --no-cache openssh python2 python3 tzdata

ENTRYPOINT [ "/etc/ssh/util/entrypoint.sh" ]
#CMD [ "/bin/sleep","5000" ]
