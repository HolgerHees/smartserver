watched_directories = [
{% for item in userdata %}{% if 'user' in userdata[item].groups %}
    "{{nextcloud_data_path}}{{item}}/",
{% endif %}{% endfor %}
]

redis_host = "redis"
redis_port = "6379"

min_preview_delay = 5
max_preview_delay = 15

cmd_file_scan = ["podman", "exec", "-it", "--user={{system_users['www'].name}}", "php", "php", "-f", "{{htdocs_path}}nextcloud/occ", "files:scan", "--all" ]
cmd_preview_generator = ["podman", "exec", "-it", "--user={{system_users['www'].name}}", "php", "php", "-f", "{{htdocs_path}}nextcloud/occ", "preview:pre-generate" ]
