<?php
$wifi_networks = [
{% for name in vault_wifi_networks %}{% if vault_wifi_networks[name]["type"] == "public" %}
    '{{name}}' => '{{vault_wifi_networks[name]["password"]}}',
{% endif %}{% endfor %}
];
