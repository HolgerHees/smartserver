var html = '<div class="service imageWatcher">';
html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
cameraSubGroup.addHtml('cameras', html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); }, 'user', 100 );
cameraSubGroup.addUrl('camera_streedside','/gallery/?sub=camera');

var subGroup = mx.Menu.getMainGroup('other').getSubGroup('devices');
subGroup.addUrl('automover', '/automowerDevice/', 'admin', 100, '{i18n_Automower}', '{i18n_Robonect}', false);
subGroup.addUrl('inverter', 'https://{{pv_inverter_garage_ip}}', 'admin', 200, '{i18n_Inverter}', '{i18n_Solar (Extern)}', true);
subGroup.addUrl('printer', 'https://{{printer_ip}}', 'user', 300, '{i18n_Laserprinter}', '{i18n_HPLaserJet}', true);
subGroup.addUrl('gateway', 'https://{{server_gateway}}', 'admin', 400, '{i18n_Router}', '{i18n_FritzBox}', true);
subGroup.addUrl('camera', 'http://{{camera_streedside_ip}}', 'admin', 400, '{i18n_Camera}', '{i18n_Streedside}', true);
