watched_directories = [
{% for item in userdata %}{% if 'user' in userdata[item].groups %}
    "{{nextcloud_data_path}}{{item}}/",
{% endif %}{% endfor %}
]

enter_cmd = [ "podman", "exec", "--user={{system_users['www'].name}}", "php", "sh", "-c" ]
notify_cmd = [ "php", "-f", "{{htdocs_path}}nextcloud/occ" ]
