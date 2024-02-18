var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
{% for device in openwrt_devices %}
subGroup.addUrl('openwrt_ap_{{device["host"]}}', ['admin'], 'https://{{device["host"]}}', { 'order': 260, 'title': '{{device["name"] if device["name"] is defined else device["host"]}}', 'info': '{i18n_OpenWRT Device}', 'icon': 'device_{{"wifi" if "ap" in device.config.roles else "switch"}}.svg', 'target': '_blank' });
{% endfor %}
