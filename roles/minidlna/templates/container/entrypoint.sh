#!/usr/bin/env bash

# Bash strict mode
set -euo pipefail
IFS=$'\n\t'

# VARs
PUID="${PUID:-100}"
PGID="${PGID:-101}"
PIDFILE="/minidlna/minidlna.pid"

# Remove old pid if it exists
[ -f $PIDFILE ] && rm -f $PIDFILE

# Change user and group identifier
groupmod --non-unique --gid "$PGID" minidlna
usermod --non-unique --uid "$PUID" minidlna

# Start daemon
exec su-exec minidlna /usr/sbin/minidlnad -f /etc/minidlna/minidlna.conf -P "$PIDFILE" -S "$@"
