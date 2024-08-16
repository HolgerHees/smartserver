#!/bin/sh

if ! id -g "$FTP_USER" >/dev/null 2>&1; then
    addgroup -g $FTP_GID -S $FTP_USER
fi

if ! id -u "$FTP_USER" >/dev/null 2>&1; then
    adduser -u $FTP_UID -D -G $FTP_USER -h /home/upload -s /bin/false --no-create-home $FTP_USER
fi

chown $FTP_USER:$FTP_USER /home/upload/ -R

echo "$FTP_USER:$FTP_PASS" | /usr/sbin/chpasswd > /dev/null 2>&1

export LOG_FILE=`grep xferlog_file /etc/vsftpd/vsftpd.conf|cut -d= -f2`

/bin/ln -sf /proc/$$/fd/1 $LOG_FILE
#/bin/ln -sf /proc/1/fd/1 $LOG_FILE

#touch $LOG_FILE
#tail -F $LOG_FILE &

PID=""
exitcode=1

stop()
{
    echo "Entrypoint - Shutting down server"
    exitcode=0

    echo "Entrypoint - Send 'TERM' to pid '$PID'"
    kill -s TERM $PID

    # No need to wait. Otherwise "Terminated" log message will occur in journald
    #echo "Entrypoint - Wait for pid '$PID'"
    #wait $PID

    #echo "Entrypoint - Exit $exitcode"
    #exit $exitcode
}

trap "stop" SIGTERM SIGINT

/usr/sbin/vsftpd /etc/vsftpd/vsftpd.conf &
PID=$!

echo "Entrypoint - Server started"

#while :; do sleep 360 & wait; done
while test -d /proc/$PID/; do sleep 1 & wait; done

if [ $exitcode -ne 0 ]; then
    echo "Entrypoint - Unexpected interruption with code '$exitcode'"
else
    echo "Entrypoint - Stopped with code '$exitcode'"
fi

exit $exitcode
