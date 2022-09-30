var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
{% for device in openwrt_devices %}
subGroup.addUrl('openwrt_ap_{{device["host"]}}', 'https://{{device["host"]}}', 'admin', 260, '{{device["name"] if device["name"] is defined else device["host"]}}', '{i18n_OpenWRT Device}', 'device_{{"wifi" if "ap" in device.config.roles else "switch"}}.svg', true);
{% endfor %}
