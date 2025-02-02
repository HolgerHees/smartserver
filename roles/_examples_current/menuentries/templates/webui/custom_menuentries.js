var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('switch_garten',  ['admin'], 'http://{{custom_switch_toolshed_ip}}', { 'order': 170, 'title': 'Switch Garten', 'info': 'TP Link', 'icon': 'device_switch.svg', 'target': '_blank' });

subGroup.addUrl('camera_strasse',  ['user'], 'https://{{custom_camera_streedside_ip}}', { 'order': 310, 'title': 'Kamera Strasse', 'info': 'Instar', 'icon': 'device_camera.svg', 'target': '_blank' });
subGroup.addUrl('camera_garten',  ['user'], 'https://{{custom_camera_toolshed_ip}}', { 'order': 310, 'title': 'Kamera Garten', 'info': 'Reolink RLC-842A', 'icon': 'device_camera.svg', 'target': '_blank' });

subGroup.addUrl('pikvm',  ['admin'], 'http://{{custom_pikvm_ip}}', { 'order': 415, 'title': 'Server KVM', 'info': 'PiKVM', 'icon': 'custom_pikvm.svg', 'target': '_blank' });
subGroup.addUrl('nuki',  ['admin'], 'http://{{custom_nuki_gateway_ip}}', { 'order': 416, 'title': 'Nuki', 'info': 'Nuki Ultra', 'icon': 'custom_nuki.svg', 'target': '_blank' });
subGroup.addUrl('watt_waechter',  ['admin'], 'http://{{custom_watt_waechter_ip}}', { 'order': 416, 'title': 'Wattwächter', 'info': 'Tasmota Watt Waechter"', 'icon': 'custom_energy.svg', 'target': '_blank' });
subGroup.addUrl('wetterstation',  ['admin'], 'http://{{custom_weatherstation_ip}}', { 'order': 416, 'title': 'Wetterstation', 'info': 'Ecowitt WS90', 'icon': 'custom_weatherstation.svg', 'target': '_blank' });

subGroup.addUrl('automover', ['admin'], 'http://{{custom_automower_ip}}', { 'order': 510, 'title': 'Automower', 'info': 'Robonect', 'icon': 'device_mower.svg', 'target': '_blank' });
subGroup.addUrl('inverter',  ['admin'], 'https://{{custom_pv_inverter_garage_ip}}', { 'order': 511, 'title': 'Solar', 'info': 'SMA Wechselrichter', 'icon': 'device_solar.svg', 'target': '_blank' });

mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('server_health', ['admin'], '//grafana.{host}/d/server-health/server-health', { 'order': 199, 'title': 'Server Health', 'info': 'Auslastung & Temperaturen', 'icon': 'custom_server_health.svg', 'callbacks': { 'url': function(url){ return mx.Grafana.applyTheme(url); } } });

var subGroup = mx.Menu.getMainGroup('admin').addSubGroup('cloud', { 'order': 400, 'title': 'Cloud', 'icon': 'custom_cloud.svg' });
subGroup.addUrl('cloud_airgradient',  ['admin'], 'https://app.airgradient.com/', { 'order': 100, 'title': 'CO2 Sensoren', 'info': 'Air Gradient', 'icon': 'cloud_airgradient.svg', 'target': '_blank' });

