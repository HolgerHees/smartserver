var subGroup = mx.Menu.getMainGroup('other').getSubGroup('devices');
subGroup.addUrl('adblocker',1000, 'admin', 'http://{{pihole_ip}}/admin/', '{i18n_AdBlocker}', '{i18n_PiHole}', true);
