var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('automover', '/automowerDevice/', 'admin', 110, '{i18n_Automower}', '{i18n_Robonect}', "proxy_mower.svg", false);
subGroup.addUrl('inverter', 'https://{{pv_inverter_garage_ip}}', 'admin', 120, '{i18n_Inverter}', '{i18n_Solar (Extern)}', "proxy_solar.svg", true);
subGroup.addUrl('printer', 'https://{{printer_ip}}', 'user', 210, '{i18n_Laserprinter}', '{i18n_HPLaserJet}', "device_printer.svg", true);
subGroup.addUrl('gateway', 'https://{{default_server_gateway}}', 'admin', 220, '{i18n_Router}', '{i18n_FritzBox}', "device_wifi.svg", true);
