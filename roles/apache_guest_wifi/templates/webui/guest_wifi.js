var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('tools');
//subGroup.addUrl('guest_wifi', '/guest_wifi/', 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', false, "guest_wifi.svg");

{% for network in vault_wifi_guest_networks %}
subGroup.addHtml('guest_wifi', '<div class="service" style="text-align: center;text-shadow: var(--submenu-shadow-service-info);"><img src="/guest_wifi/?name={{network}}"><div>{{network}}</div></div>', function(){}, 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', "guest_wifi.svg");
{% endfor %}
