<?php
$wifi_networks = [
{% for name in guest_wifi_networks %}
    '{{name}}' => '{{guest_wifi_networks[name]["password"]}}',
{% endfor %}
];
