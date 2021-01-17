FROM alpine:{{image_version}}

RUN apk add --no-cache --update wireguard-tools
 
ENTRYPOINT [ "/etc/wireguard/util/startup.sh" ]
