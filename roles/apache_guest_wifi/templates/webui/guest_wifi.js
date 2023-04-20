var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('tools');
//subGroup.addUrl('guest_wifi', '/guest_wifi/', 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', false, "guest_wifi.svg");

{% for name in vault_wifi_networks %}{% if vault_wifi_networks[name]["type"] == "public" %}
subGroup.addHtml('guest_wifi', '<div class="service" style="text-align: center;text-shadow: var(--submenu-shadow-service-info);"><img src="/guest_wifi/?name={{name}}"><div>{{name}}</div></div>', function(){}, 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', "guest_wifi.svg");
{% endif %}{% endfor %}
