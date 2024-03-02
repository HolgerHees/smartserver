## Hints

This guide assumes

* that the first md device is called `/dev/md0`
* that `/dev/md0` is a RAID-1 array
* that `/dev/md0` consists of the following components:
  * `/dev/sda1`
  * `/dev/sdb1`
* that `/dev/sdb1` is the broken md component

## Replacing a hard drive that is only used in an md device (RAID array).

### Determine which md component was detected as faulty

Please first check which hard drive was recognized as faulty by calling the following command.

```
# cat /proc/mdstat
```

Its output looks similar to the following (abridged):

```
md0 : active raid1 sdb1[1](F) sda1[0]
      *** blocks [2/1] [_U]
```

You can see from the `(F)` that `sdb1` was detected as the faulty partition / device.

Alternatively you can call the following command:

```
# mdadm --detail /dev/md0
```

### Identify the device by flashing LED

```
while :; do smartctl -a /dev/sdb1;
```

### Removing the faulty partition from the RAID array

Remove the faulty partition with the following command:

```
# mdadm --remove /dev/md0 /dev/sdb1
```

If the faulty hard drive has several partitions, all of them must be removed first.

```
# mdadm --remove /dev/md1 /dev/sdb2
# mdadm --remove /dev/md2 /dev/sdb3
# mdadm --remove /dev/md3 /dev/sdb4
```

### Removing a non-broken partition

If a non-faulty hard drive has to be replaced, for example because the first symptoms appear that it will break soon, the partitions must first changed into the fail state using the following command.

```
# mdadm --manage /dev/md0 --fail /dev/sdb1
```

Otherwise the removal using `# mdadm --remove /dev/md0 /dev/sdb1` would fail with the error message `mdadm: hot remove failed for /dev/sdb1: Device or resource busy`.

### Partitioning the new hard drive

The new hard drive must be partitioned exactly like the old hard drive. The easiest way to do this is to copy the partition tables.

Beforehand, you should use the following command to find out whether MBR (usually for hard drives < 2GB) or GPT (usually for hard drives > 2GB) is used as the partition table.

```
# gdisk -l /dev/sda
```

Its output looks similar to the following (abridged):

```
Partition table scan:
  MBR: protective
  BSD: not present
  APM: not present
  GPT: present
```

or

```
Partition table scan:
  MBR: MBR only
  BSD: not present
  APM: not present
  GPT: not present
```

Here either `GPT: not present` stands for MBR or `GPT: present` stands for GPT.

Below are the commands, depending on the previously determined type, to copy the partition table.

***MBR Partition Table***

```
# sfdisk -d /dev/sda | sfdisk /dev/sdb
```

or

```
# sfdisk --dump /dev/sda > sda_parttable_mbr.bak
# sfdisk /dev/sdb < sda_parttable_mbr.bak
```

***GPT partition table with subsequent generation of a new UUID***

```
# sgdisk --backup=sda_parttable_gpt.bak /dev/sda
# sgdisk --load-backup=sda_parttable_gpt.bak /dev/sdb
# sgdisk -G /dev/sdb
```

***Please make sure that `/dev/sda` is the correctly functioning hard drive and `/dev/sdb` is the defective hard drive!***

### Adding the new partition to the RAID array

Add the new partition using the following command:

```
# mdadm --add /dev/md0 /dev/sdb1
```

and check whether the process was successful with the following command:

```
# cat /proc/mdstat
```

If successful, you will see the status of the rebuild:

```
md0 : active raid1 sdb1[1] sda1[0]
      *** blocks [2/1] [_U]
      [>.............] = *% (*/*) finish=*min speed=*K/sec
```

### Reinstall bootloader (GPT partition)

Since the serial number of the disk has changed, the device map is first regenerated in GRUB2 with the following command:

```
# grub-mkdevicemap -n
```

If you carry out the repair in the booted system, with GRUB2 a grub install on the new hard drive is sufficient with the following command

```
# grub-install /dev/sdb
```
