{% if authenticated_ip_addresses | length > 0 %}
        Require ip {{ authenticated_ip_addresses | join(' ') }}
{% endif %}
        Require ip 172.0.0.0/8
        Require local
