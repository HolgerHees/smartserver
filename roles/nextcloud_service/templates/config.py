watched_directories = [
    "{{nextcloud_data_path}}admin/files/"
{% for item in userdata %}{% if 'user' in userdata[item].groups %}
    , "{{nextcloud_data_path}}{{item}}/files/"
{% endif %}{% endfor %}
]

redis_host = "redis"
redis_port = "6379"

min_preview_delay = 5
max_preview_delay = 15

process_container_uid = "{{system_users['www'].id}}"

cmd_file_scan = ["php", "-f", "{{htdocs_path}}nextcloud/occ", "files:scan", "--all" ]
cmd_inotify_listener = ["php", "-f", "{{htdocs_path}}nextcloud/occ", "files_notify_redis:primary", "-v", "inotify" ]
cmd_preview_generator = ["php", "-f", "{{htdocs_path}}nextcloud/occ", "preview:pre-generate" ]

#cmd_memorial_index = ["php", "-f", "{{htdocs_path}}nextcloud/occ", "memories:index" ]
#cmd_memorial_places = ["php", "-f", "{{htdocs_path}}nextcloud/occ", "memories:places-setup" ]

#cmd_file_scan = ["podman", "exec", "-it", "--user={{system_users['www'].name}}", "php", "php", "-f", "{{htdocs_path}}nextcloud/occ", "files:scan", "--all" ]
#cmd_preview_generator = ["podman", "exec", "-it", "--user={{system_users['www'].name}}", "php", "php", "-f", "{{htdocs_path}}nextcloud/occ", "preview:pre-generate" ]
#cmd_inotify_listener = ["podman", "exec", "-it", "--user={{system_users['www'].name}}", "php", "php", "-f", "{{htdocs_path}}nextcloud/occ", "files_notify_redis:primary", "-v", "inotify" ]
