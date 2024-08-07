FROM alpine:{{alpine_version}}

RUN apk add --update samba-common-tools samba-client samba-server tzdata \
  && addgroup -g {{system_groups['www'].id}} -S {{system_groups['www'].name}} \
  && adduser -u {{system_users['www'].id}} -D -G {{system_groups['www'].name}} -h {{nextcloud_data_path}} -s /bin/false --no-create-home {{system_users['www'].name}}

ENTRYPOINT ["smbd", "--foreground", "--debuglevel=1", "--debug-stdout", "--no-process-group"]
