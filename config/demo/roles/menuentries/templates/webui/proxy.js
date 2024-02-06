var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('printer', 'https://{{custom_printer_ip}}', 'user', 210, '{i18n_Laserprinter}', '{i18n_HPLaserJet}', "device_printer.svg", true);
subGroup.addUrl('gateway', 'https://{{default_server_gateway}}', 'admin', 220, '{i18n_Router}', '{i18n_FritzBox}', "device_wifi.svg", true);
