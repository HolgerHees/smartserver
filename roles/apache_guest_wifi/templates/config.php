<?php
$wifi_networks = [
{% for name in wifi_networks %}{% if wifi_networks[name]["type"] == "public" %}
    '{{name}}' => '{{wifi_networks[name]["password"]}}',
{% endif %}{% endfor %}
];
