var html = '<div class="service imageWatcher">';
html += '<div style="cursor:pointer" onclick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
cameraSubGroup.addUrl('camera_streedside','/gallery/?sub=camera');

var subGroup = mx.Menu.getMainGroup('other').getSubGroup('devices');
subGroup.addUrl('automover',100, 'admin', '/automowerDevice/', '{i18n_Automower}', '{i18n_Robonect}', false);
subGroup.addUrl('inverter',200, 'admin', 'https://{{pv_inverter_garage_ip}}', '{i18n_Inverter}', '{i18n_Solar (Extern)}', true);
subGroup.addUrl('printer',300, 'user', 'https://{{printer_ip}}', '{i18n_Laserprinter}', '{i18n_HPLaserJet}', true);
subGroup.addUrl('gateway',400, 'admin', 'https://{{server_gateway}}', '{i18n_Router}', '{i18n_FritzBox}', true);
subGroup.addUrl('camera',400, 'admin', 'http://{{camera_streedside_ip}}', '{i18n_Camera}', '{i18n_Streedside}', true);
