name            = '{{item.name}}'
password        = {% if 'password' in item %}'{{item.password | replace("\\", "\\\\") | replace("'", "\\'") }}'{% else %}False{% endif %}

bandwidth_limit = {% if 'bandwidth_limit' in item %}'{{item.bandwidth_limit}}'{% else %}False{% endif %}


lockfile        = "{{global_tmp}}backup_sync_{{item.name}}.lock"
logfile         = "{{global_log}}backup_sync/{{item.name}}_[DATETIME].log"

destination     = '{{item.destination}}'

sources           = [
{% for source in item.sources %}
    {
        "name": {% if 'name' in source %}'{{source.name}}'{% else %}False{% endif %},
        "path": '{{source.path}}',
        "options": {% if 'options' in source %}['{{source.options | join("','")}}']{% else %}False{% endif %},
        "filter": {% if 'filter' in source %}['{{source.filter | join("','")}}']{% else %}False{% endif %}

    },
{% endfor %}
]