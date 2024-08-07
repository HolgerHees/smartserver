FROM alpine:{{alpine_version}}

RUN apk add --no-cache --update nfs-utils tzdata

#RUN echo 'hosts: files dns' >> /etc/nsswitch.conf

RUN mkdir /var/lib/nfs/v4recovery

#openrc musl-nscd
#openrc

#RUN mkdir -p /var/lib/nfs/rpc_pipefs                                                     && \
#    mkdir -p /var/lib/nfs/v4recovery                                                     && \
#    echo "rpc_pipefs  /var/lib/nfs/rpc_pipefs  rpc_pipefs  defaults  0  0" >> /etc/fstab && \
#    echo "nfsd        /proc/fs/nfsd            nfsd        defaults  0  0" >> /etc/fstab

#RUN apk add --no-cache --update git cmake make g++ bison flex krb5-dev userspace-rcu-dev nfs-utils-dev libnsl-dev
#RUN git clone --recursive https://github.com/nfs-ganesha/nfs-ganesha.git
#RUN git checkout tags/V3.2
#RUN git submodule update --init
#RUN mkdir build && 
#RUN ccmake -DUSE_FSAL_VFS=ON -DUSE_GSS=OFF -DUSE_DBUS=OFF -DUSE_FSAL_CEPH=OFF -DUSE_FSAL_GLUSTER=OFF -DUSE_FSAL_GPFS=OFF -DUSE_FSAL_LIZARDFS=OFF -DUSE_FSAL_LUSTRE=OFF -DUSE_FSAL_MEM=OFF -DUSE_FSAL_NULL=OFF -DUSE_FSAL_PANFS=OFF -DUSE_FSAL_PROXY_V3=OFF -DUSE_FSAL_PROXY_V4=OFF -DUSE_FSAL_RGW=OFF -DUSE_FSAL_XFS=OFF -DUSE_RADOS_RECOV=OFF -DRADOS_URLS=OFF -DUSE_CAPS=OFF -D_MSPAC_SUPPORT=OFF -DUSE_9P=OFF -DALLOCATOR=libc ../src

#RUN cmake -DUSE_FSAL_VFS=ON -DUSE_GSS=OFF -DUSE_DBUS=OFF -DUSE_FSAL_CEPH=OFF -DUSE_FSAL_GLUSTER=OFF -DUSE_FSAL_GPFS=OFF -DUSE_FSAL_LIZARDFS=OFF -DUSE_FSAL_LUSTRE=OFF -DUSE_FSAL_MEM=OFF -DUSE_FSAL_NULL=OFF -DUSE_FSAL_PANFS=OFF -DUSE_FSAL_PROXY_V3=OFF -DUSE_FSAL_PROXY_V4=OFF -DUSE_FSAL_RGW=OFF -DUSE_FSAL_XFS=OFF -DUSE_RADOS_RECOV=OFF -DRADOS_URLS=OFF -DUSE_CAPS=OFF -D_MSPAC_SUPPORT=OFF -DUSE_9P=OFF -DALLOCATOR=libc ../src

# -DUSE_RADOS_RECOV=OFF -DRADOS_URLS=OFF 
 
ENTRYPOINT [ "/etc/cloud_nfs/util/startup.sh" ]

EXPOSE 2049/tcp
EXPOSE 2049/udp
