#!/usr/bin/python3
# Export KeePass file to Nextcloud Passwords backup file format
#
# The file can then be imported in Nextcloud Passwords "Backup & Restore" > "Restore/import" > Choose Format "Database backup"
#
# Prerequisites
# --------------
# pip3 install pykeepass
# 
# Usage
# -----
# python3 keepass-to-nextcloud-passwords.py passfile.kbdx
#
# Author: Holger Hees

from pykeepass import PyKeePass
import getpass
import sys
import json

# load database
kp = PyKeePass(sys.argv[1], password=getpass.getpass())

def group_to_bw_folder_json(folder):
    return {
        "id": str(folder.uuid),
        "label": folder.name,
        "parent": str(folder.parentgroup.uuid) if folder.parentgroup and folder.parentgroup.name != "Root" else "00000000-0000-0000-0000-000000000000"
    }

def entry_to_bw_json(entry):
    if entry.notes and len(entry.notes)>4096:
        print("Notes of {} too long for import to nextcloud passwords".format(entry.title))

    data = {
        "id": str(entry.uuid),
        "label": entry.title if entry.title != None else "",
        "url": entry.url if entry.url != None else "",
        "folder": str(entry.group.uuid) if entry.group and entry.group.name != "Root" else "00000000-0000-0000-0000-000000000000",
        "username":entry.username if entry.username != None else "",
        "password": entry.password if entry.password != None else "",
        "notes": entry.notes if entry.notes != None else ""
        }

    custom_fields = []
    for key, value in entry.custom_properties.items():
        custom_fields.append({"label":key,"type":"text","value":value})

    data["customFields"] = custom_fields

    return data


def export(kp):
    items = []
    for i in kp.entries:
        items.append(entry_to_bw_json(i))

    folders = []
    for g in kp.groups:
        folders.append(group_to_bw_folder_json(g))
    
    with open('./nextcloud-passwords-backup.json','w') as f:
        json.dump({
            "encrypted": False,
            "version": 3,
            "folders": folders,
            "passwords": items
        },f, indent=2)

export(kp)

