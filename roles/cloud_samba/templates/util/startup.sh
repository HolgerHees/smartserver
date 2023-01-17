#!/bin/sh
cd /etc/samba

source ./peers

isServerReachable()
{
    eval "samba_server_ip=\$samba_server_ip_$1"
    echo "check reachability of $samba_server_ip"
    nc -w 1 -z $samba_server_ip 445
    STATUS=$( echo $? )
    return $STATUS
}

stop()
{
    echo "SIGTERM caught, shutting down..."
    
    echo "unmount samba shares"
    for name in $peers
    do
        isServerReachable $name
        if [[ $? == 0 ]]
        then
            echo "unmount /cloud/remote/$name"
            umount -l /cloud/remote/$name > /dev/null 2>&1
        else
            echo "forced unmount /cloud/remote/$name"
            umount -f -l /cloud/remote/$name > /dev/null 2>&1
        fi
    done

    echo "terminating samba process(es)"
    #pid1=`pidof sambad`
    #pid2=`pidof winbind`
    #kill -TERM $pid1 $pid2 > /dev/null 2>&1

    pid1=`pidof smbd`
    kill -TERM $pid1 > /dev/null 2>&1

    echo "done"
    exit
}

exportLocalShares()
{
    if [ -n "$peers" ]
    then
        echo "starting smbd"

        rm /var/log/samba/log* 2>/dev/null &

        #smbd --foreground --log-stdout
        smbd --foreground --debuglevel=1 --debug-stdout --no-process-group -l /var/log/samba/ &

        sleep 1

        pid=`pidof smbd`
        if [ -z "$pid" ]; then
          echo "startup of smbd failed"
          exit 1
        fi

        echo "...done"
    else
        echo "skipped local share exports"
    fi
}

mountRemoteShares()
{
    if [ -n "$peers" ]
    then
        echo "mount samba shares..."
        x=1
        while :
        do
            mount_state=0
            
            for name in $peers
            do
                if ! mountpoint -q /cloud/remote/$name
                then
                    isServerReachable $name
                    #eval "nfs_server_ip=\$nfs_server_ip_$name"
                    #echo "check reachability of $nfs_server_ip"
                    #nc -w 1 -z $nfs_server_ip 2049
                    #STATUS=$( echo $? )
                    #if [[ $STATUS == 0 ]]
                    if [[ $? == 0 ]]
                    then
                        echo "mount /cloud/remote/$name"
                        mount /cloud/remote/$name
                    else
                        mount_state=1
                    fi
                fi
            done
            
            if [ $mount_state == 0 ]
            then
                echo "...done"
                break
            else
                sleep 15 & wait $!
            fi
        done
    else
        echo "skipped remote share mounts"
    fi
}

trap "stop" SIGTERM SIGINT

exportLocalShares

#mountRemoteShares

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1
