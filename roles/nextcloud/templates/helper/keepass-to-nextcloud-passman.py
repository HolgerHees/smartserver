#!/usr/bin/python3
# Export KeePass file to Nextcloud Passwords backup file format
#
# The file can then be imported in Nextcloud Passman "Settings" > "Import" > Choose Impot Type "Database backup"
#
# Prerequisites
# --------------
# pip3 install pykeepass
# 
# Usage
# -----
# python3 keepass-to-nextcloud-passwords.py passfile.kbdx user_id
#
# Author: Holger Hees

from pykeepass import PyKeePass
import getpass
import sys
import json

# load database
kp = PyKeePass(sys.argv[1], password=getpass.getpass())
user_id = sys.argv[2]

def group_to_tags(group):
    tags = []
    tags.append(group.name)
    if group.parentgroup and group.parentgroup.name != "Root":
        tags = tags + group_to_tags(group.parentgroup)
    return tags

def entry_to_bw_json(user_id, entry, counter):
    if entry.notes and len(entry.notes)>4096:
        print("Notes of {} too long for import to nextcloud passman".format(entry.title))

    is_deleted = False

    if entry.group and entry.group.name != "Root":
        for tag in group_to_tags(entry.group):
            if tag == "keys":
                continue
            elif tag == "Recycle Bin":
                is_deleted = True
                continue
            #tags.append({"text": tag})

    tags = []
    if entry.tags:
        for tag in entry.tags:
            tags.append({"text": tag.strip()})

    custom_fields = []
    for key, value in entry.custom_properties.items():
        custom_fields.append({"label":key,"field_type":"text","value":value, "secret": False})

    data = {
        "credential_id": counter,
        "guid": str(entry.uuid),
        "user_id": user_id,
        "label": entry.title if entry.title != None else "",
        "description": entry.notes if entry.notes != None else "",
        "created": int(entry.ctime.timestamp()),
        "changed": int(entry.mtime.timestamp()),
        "tags": tags,
        "email": "",
        "username":entry.username if entry.username != None else "",
        "password": entry.password if entry.password != None else "",
        "url": entry.url if entry.url != None else "",
        "icon": None,
        "renew_interval": None,
        "expire_time": 0,
        "delete_time": 0 if not is_deleted else int(entry.mtime.timestamp()),
        "files": [],
        "custom_fields": custom_fields,
        "otp": {},
        "hidden": 0,
        "compromised": False
    }

    return data


def export(kp):
    groups = {}
    for g in kp.groups:
        groups[g.uuid] = g

    counter = 1
    items = []
    for i in kp.entries:
        item = entry_to_bw_json(user_id, i,counter)
        if item is None:
            continue
        items.append(item)
        counter += 1

    with open('./nextcloud-passman-backup.json','w') as f:
        json.dump(items, f, indent=2)

export(kp)

