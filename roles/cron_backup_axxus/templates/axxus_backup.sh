#!/bin/sh

DATUM=$(date '+%Y.%m.%d')

LOGVERZ="{{local_backup_path}}axxus.de/logs/"
BACKUP="{{local_backup_path}}axxus.de/backup/"

SOURCE="root@www.axxus.de:/backup/"
DESTINATION="{{local_backup_path}}axxus.de/current/"

rsync -avz --delete --copy-unsafe-links --backup --backup-dir=$BACKUP$DATE $SOURCE $DESTINATION >> $LOGVERZ$DATUM".log"
#rsync -avz --delete --progress --copy-unsafe-links --backup --backup-dir=$BACKUP$DATE $SOURCE $DESTINATION

