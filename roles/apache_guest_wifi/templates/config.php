<?php
$wifi_networks = [
{% for network in vault_wifi_guest_networks %}
    '{{network}}' => '{{vault_wifi_guest_networks[network]}}',
{% endfor %}
];
