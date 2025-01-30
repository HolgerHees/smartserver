var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
{% for device in network_devices %}
{% set device_name=(device["name"] if device["name"] is defined else device["host"]) %}
{% set device_info=(device.config.webui.info if 'config' in device and 'webui' in device.config and 'info' in device.config.webui else '') %}
{% set device_is_ap=(true if 'config' in device and 'openwrt' in device.config and  "ap" in device.config.openwrt.deployment_roles else false) %}
{% set device_order=(device.config.webui.order if 'config' in device and 'webui' in device.config and 'order' in device.config.webui else (250 if device_is_ap else 150)) %}
{% set device_icon=(device.config.webui.icon if 'config' in device and 'webui' in device.config and 'icon' in device.config.webui else ('device_wifi.svg' if device_is_ap else 'device_switch.svg')) %}

subGroup.addUrl('network_device_{{device["host"]}}', ['admin'], 'https://{{device["host"]}}', { 'order': {{device_order}}, 'title': '{{device_name}}', 'info': '{{device_info}}', 'icon': '{{device_icon}}', 'target': '_blank' });
{% endfor %}
