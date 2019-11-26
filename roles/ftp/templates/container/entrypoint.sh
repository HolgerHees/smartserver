#!/bin/sh

addgroup -g $FTP_GID -S $FTP_USER
adduser -u $FTP_UID -D -G $FTP_USER -h /home/$FTP_USER -s /bin/false  $FTP_USER
chown $FTP_USER:$FTP_USER /home/$FTP_USER/ -R

echo "$FTP_USER:$FTP_PASS" | /usr/sbin/chpasswd > /dev/null 2>&1

cp /etc/vsftpd/vsftpd.conf_or /etc/vsftpd/vsftpd.conf

if [[ "$PASV_ENABLE" == "YES" ]]; then
  echo "PASV is enabled"
  echo "pasv_enable=YES" >> /etc/vsftpd/vsftpd.conf
  echo "pasv_max_port=$PASV_MAX" >> /etc/vsftpd/vsftpd.conf
  echo "pasv_min_port=$PASV_MIN" >> /etc/vsftpd/vsftpd.conf
  echo "pasv_address=$PASV_ADDRESS" >> /etc/vsftpd/vsftpd.conf
else
  echo "pasv_enable=NO" >> /etc/vsftpd/vsftpd.conf
fi

if [[ "$ONLY_UPLOAD" == "YES" ]]; then
  echo "Only uploads allowed"
  echo "download_enable=NO" >> /etc/vsftpd/vsftpd.conf
  #echo "ftpd_banner=Welcome to FTP Server. Note: this FTP server only accepts upload." >> /etc/vsftpd/vsftpd.conf
elif [[ "$ONLY_DOWNLOAD" == "YES" ]]; then
  echo "Only downloads allowed"
  #echo "ftpd_banner=Welcome to FTP Server. Note: this FTP server only accepts download." >> /etc/vsftpd/vsftpd.conf
  sed -i 's/write_enable=YES/write_enable=NO/g' /etc/vsftpd/vsftpd.conf
else
  echo "ftpd_banner=Welcome to FTP Server" >> /etc/vsftpd/vsftpd.conf
fi

echo "local_umask=$UMASK" >> /etc/vsftpd/vsftpd.conf

export LOG_FILE=`grep xferlog_file /etc/vsftpd/vsftpd.conf|cut -d= -f2`

echo "$LOG_FILE" >> /etc/logrotate.d/vsftpd
echo "{" >> /etc/logrotate.d/vsftpd
echo "	create 640 root adm" >> /etc/logrotate.d/vsftpd
echo "	# ftpd doesn't handle SIGHUP properly" >> /etc/logrotate.d/vsftpd
echo "	missingok" >> /etc/logrotate.d/vsftpd
echo "	notifempty" >> /etc/logrotate.d/vsftpd
echo "	rotate 4" >> /etc/logrotate.d/vsftpd
echo "	weekly" >> /etc/logrotate.d/vsftpd
echo "}" >> /etc/logrotate.d/vsftpd

#/bin/ln -sf /dev/stdout $LOG_FILE

touch $LOG_FILE
tail -F $LOG_FILE &

echo "Server started"
/usr/sbin/vsftpd /etc/vsftpd/vsftpd.conf
 
