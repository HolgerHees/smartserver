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
import uuid

# https://htmlcolorcodes.com/color-names/
colors = [
    "#FF0000", # red
    "#FFC0CB", # pink
    "#C71585", # MediumVioletRed
    "#FFA07A", # LightSalmon
    "#FF6347", # tomato
    "#FFD700", # gold
    "#F0E68C", # khaki
    "#DDA0DD", # plum
    "#E6E6FA", # lavender
    "#8A2BE2", # blue violet
    "#8B008B", # dark magenta
    "#32CD32", # lime green
    "#2E8B57", # sea green
    "#9ACD32", # yellow green
    "#8FBC8B", # dark sea green
    "#008080", # teal
    "#40E0D0", # turquoise
    "#4682B4", # steelblue
    "#87CEEB", # sky blue
    "#4169E1", # royal blue
    "#000080", # navy
    "#DEB887", # burly wood
    "#CD853F", # peru
    "#A52A2A", # brown
    "#F5F5DC", # beige
    "#808080", # gray
#    "#FFFFFF",
#    "#C0C0C0",
#    "#808080",
#    "#000000",
#    "#FF0000",
#    "#800000",
#    "#FFFF00",
#    "#808000",
#    "#00FF00",
#    "#008000",
#    "#00FFFF",
#    "#008080",
#    "#0000FF",
#    "#000080",
#    "#FF00FF",
#    "#800080",
]

deleted_tag_label = "_Gelöscht"
root_folder_label = "Passwörter"

# load database
kp = PyKeePass(sys.argv[1], password=getpass.getpass())

#def group_to_bw_folder_json(folder):
#    return {
#        "id": str(folder.uuid),
#        "label": folder.name,
#        "parent": str(folder.parentgroup.uuid) if folder.parentgroup and folder.parentgroup.name != "Root" else "00000000-0000-0000-0000-000000000000"
#    }


def group_to_tags(group):
    tags = []
    tags.append(group.name)
    if group.parentgroup and group.parentgroup.name != "Root":
        tags = tags + group_to_tags(group.parentgroup)
    return tags

def entry_to_bw_json(entry, all_tags, parent_folder_uuid):
    if entry.notes and len(entry.notes)>4096:
        print("Notes of {} too long for import to nextcloud passwords".format(entry.title))

#        "label": entry.title if entry.title != None else "",
#        "description": entry.notes if entry.notes != None else "",
#        "url": entry.url if entry.url != None else "",
#        "tags": tags,
#        "username":entry.username if entry.username != None else "",
#        "password": entry.password if entry.password != None else "",
#        "custom_fields": custom_fields,
#        "created": int(entry.ctime.timestamp()),
#        "changed": int(entry.mtime.timestamp()),

#    data = {
#        "credential_id": counter,
#        "guid": str(entry.uuid),
#        "user_id": user_id,
#        "email": "",
#        "icon": None,
#        "renew_interval": None,
#        "expire_time": 0,
#        "delete_time": 0 if not is_deleted else int(entry.mtime.timestamp()),
#        "files": [],
#        "otp": {},
#        "hidden": 0,
#        "compromised": False
#    }

    tags = []
    if entry.tags:
        for tag in entry.tags:
            tag = tag.strip()
            tags.append(all_tags[tag]["id"])

    if entry.group and entry.group.name != "Root":
        for tag in group_to_tags(entry.group):
            if tag == "Recycle Bin":
                tags.append(all_tags[deleted_tag_label]["id"])
                break

    custom_fields = []
    for key, value in entry.custom_properties.items():
        custom_fields.append({"label":key,"type":"text","value":value})

    data = {
        "id": str(entry.uuid),
        "folder": parent_folder_uuid,
        "tags": tags,
        "label": entry.title if entry.title != None else "",
        "notes": entry.notes if entry.notes != None else "",
        "url": entry.url if entry.url != None else "",
        "username":entry.username if entry.username != None else "",
        "password": entry.password if entry.password != None else "",
        "customFields": custom_fields,
        "edited": int(entry.mtime.timestamp())
#        "created": int(entry.ctime.timestamp()),
#        "updated": int(entry.mtime.timestamp()),
#        "trashed": is_deleted,
        }

    custom_fields = []
    for key, value in entry.custom_properties.items():
        custom_fields.append({"label":key,"type":"text","value":value})

    data["customFields"] = custom_fields

    return data


def export(kp):
    tags = {deleted_tag_label: {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, deleted_tag_label)),
        "label": deleted_tag_label,
        "color": colors[0]
    }}
    total_colors = len(colors)
    for entry in kp.entries:
        if entry.tags:
            for tag in entry.tags:
                tag = tag.strip()
                index = len(tags)
                while index >= total_colors:
                    index -= total_colors
                if tag not in tags:
                    tags[tag] = {
                        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, tag)),
                        "label": tag,
                        "color": colors[index]
                    }

    folder_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, root_folder_label))
    folders = [{
        "id": folder_uuid,
        "label": root_folder_label,
        "parent": "00000000-0000-0000-0000-000000000000"
   }]
#    for g in kp.groups:
#        folders.append(group_to_bw_folder_json(g))

    items = []
    for i in kp.entries:
        items.append(entry_to_bw_json(i, tags, folder_uuid))

    with open('./nextcloud-passwords-backup.json','w') as f:
        json.dump({
            "encrypted": False,
            "version": 3,
            "folders": folders,
            "passwords": items,
            "tags": list(tags.values())
        },f, indent=2)

export(kp)

