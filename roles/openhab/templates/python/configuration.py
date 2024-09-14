# -*- coding: utf-8 -*-
LOG_PREFIX = "jsr223.jython"

userConfigs = {
{% for username in userdata %}{% if userdata[username].openhab is defined %}
  {% if loop.index > 1 %},{% endif %}"{{username}}": { "state_item": {% if userdata[username].openhab.state_item is defined %}"{{userdata[username].openhab.state_item}}"{% else %}None{% endif %}, "notification_config": {% if userdata[username].openhab.notification_config is defined %}[ '{{userdata[username].openhab.notification_config | join("','") }}' ]{% else %}None{% endif %}, "is_admin": {{ 'True' if 'admin' in userdata[username].groups else 'False'}}, "name": "{{userdata[username].name}}" }
{% endif %}{% endfor %}
}

customConfigs = {{ openhab_custom_value_map | to_nice_json }}
