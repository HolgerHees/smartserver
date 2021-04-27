FROM alpine:{{image_version}}

RUN apk add --no-cache --update wireguard-tools iperf3
 
ENTRYPOINT [ "/etc/wireguard/util/startup.sh" ]
