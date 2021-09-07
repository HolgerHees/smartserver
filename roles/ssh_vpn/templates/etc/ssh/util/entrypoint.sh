#!/bin/sh

if ! id -g vpn >/dev/null 2>&1; then
    addgroup -g $SSH_GID -S vpn
fi

if ! id -u "$SSH_USERNAME" >/dev/null 2>&1; then
    #mkdir /home/$SSH_USERNAME
    #mkdir /home/$SSH_USERNAME/.ssh
    adduser -u $SSH_UID -D -G vpn -h /home/$SSH_USERNAME -s /bin/sh --no-create-home $SSH_USERNAME
    chown -R vpn.vpn /home/$SSH_USERNAME

    echo "${SSH_USERNAME}:${SSH_PASSWORD}" | chpasswd
fi

# generate host keys if not present
ssh-keygen -A

# do not detach (-D), log to stderr (-e), passthrough other arguments
exec /usr/sbin/sshd -D -e 2>&1
