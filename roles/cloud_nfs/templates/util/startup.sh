#!/bin/sh
cd /etc/cloud_nfs

source ./peers

#https://wiki.archlinux.org/index.php/NFS/Troubleshooting

#rpcdebug -m nfsd all

#https://www.heise.de/ct/artikel/NFSv4-unter-Linux-221582.html?seite=all
# check cat /proc/net/rpc/auth.unix.ip/content

isServerReachable()
{
    eval "nfs_server_ip=\$nfs_server_ip_$1"
    echo "check reachability of $nfs_server_ip"
    nc -w 1 -z $nfs_server_ip 2049
    STATUS=$( echo $? )
    return $STATUS
}

stop()
{
    echo "SIGTERM caught, shutting down..."
    
    echo "unmount nfs shares"
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

    echo "terminating nfs process(es)"
    /usr/sbin/exportfs -uav
    /usr/sbin/rpc.nfsd 0
    pid1=`pidof rpc.nfsd`
    pid2=`pidof rpc.mountd`
    #pid3=`pidof rpc.statd`
    # For IPv6 bug:
    #pid4=`pidof rpcbind`
    #kill -TERM $pid1 > /dev/null 2>&1
    kill -TERM $pid1 $pid2 > /dev/null 2>&1

    echo "done"
    exit
}

exportLocalShares()
{
    if [ -n "$peers" ]
    then
        #echo "open nlockmgr ports"
        #mount -t nfsd nfsd /proc/fs/nfsd
        #echo 'fs.nfs.nlm_tcpport=32768' >> /etc/sysctl.conf
        #echo 'fs.nfs.nlm_udpport=32768' >> /etc/sysctl.conf
        #sysctl -p > /dev/null
        
        # Normally only required if v3 will be used
        # But currently enabled to overcome an NFS bug around opening an IPv6 socket
        #echo "starting rpcbind"
        #/sbin/rpcbind -w
        #echo "starting idmapd"
        #/usr/sbin/rpc.idmapd
        #echo "starting statd"
        #/sbin/rpc.statd
        ##-p 32765 -o 32766
        
        # Kerberos
        #/usr/sbin/rpc.svcgssd -v
        #/usr/sbin/rpc.gssd -v
        
        echo "starting nfs"
        /usr/sbin/rpc.nfsd --debug --no-nfs-version 3
        #sleep 1
        #/usr/sbin/rpc.nfsd 0
        #sleep 1
        #/usr/sbin/rpc.nfsd --debug --no-nfs-version 3
        
        echo "starting exportfs"
        FS_RESULT=$(/usr/sbin/exportfs -arv)
        if [ -z "$FS_RESULT" ]
        then
          echo "export validation failed"
          exit 1
        else
          echo $FS_RESULT
        fi
        
        #echo "starting mountd"
        /usr/sbin/rpc.mountd --debug all --no-nfs-version 2 --no-nfs-version 3
        # --exports-file /etc/exports

        # check if nfc is running
        pid=`pidof rpc.mountd`
        if [ -z "$pid" ]; then
          echo "startup of nfs failed"
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
        echo "mount nfs shares..."
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
                sleep 15 & wait
            fi
        done
    else
        echo "skipped remote share mounts"
    fi
}

trap "stop" SIGTERM SIGINT

exportLocalShares

mountRemoteShares

# wait forever or until we get SIGTERM or SIGINT
while :; do sleep 360 & wait; done

exit 1

