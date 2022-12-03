NAME=$1
TARGET=$2

LOCK_FILE="{{global_tmp}}cloud_backup_$NAME.lock"
LOG_FILE="{{global_log}}cloud_backup/cloud_backup_$NAME.log"

SOURCE="{{global_lib}}cloud_backup"

BW_LIMIT="02:00,30M 05:00,20M 06:00,5M 23:00,10M"

mountpoint -q $TARGET 
if [ $? -eq 1 ] 
then
    >&2 echo "$TARGET not mounted"
    exit 1
fi

/usr/bin/flock -n "$LOCK_FILE" /opt/rclone/rclone --log-file="$LOG_FILE" --log-level INFO --bwlimit="$BW_LIMIT" --copy-links --config=/opt/rclone/rclone.config --crypt-remote="$TARGET" sync "$SOURCE" backup:
if [ $? -eq 1 ] 
then
    >&2 echo "Cloud backup '$NAME' was not successful"
    exit 1
else
    echo "Cloud backup '$NAME' was successful"
    exit 0
fi

