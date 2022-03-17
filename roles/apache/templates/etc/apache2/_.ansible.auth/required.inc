{% for username in userdata %}{% if item in userdata[username].groups %}
{% if vault_openid_connect_url != 'None' %}Require claim email:{{userdata[username].email}}
{% endif %}
Require user {{username}}
{% endif %}{% endfor %}
{% if authenticated_ip_addresses | length > 0 %}
Require ip {{ authenticated_ip_addresses | join(' ') }}
{% endif %}
Require ip 172.0.0.0/8
Require local
