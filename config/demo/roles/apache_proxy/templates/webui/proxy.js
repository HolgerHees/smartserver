var html = '<div class="service imageWatcher">';
html += '<div><a href="/cameraStrasseDevice/" target="_blank"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></a></div>';
html += '<div><a href="/automowerDevice/" target="_blank"><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></a></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
cameraSubGroup.addHtml('cameras',100, html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); });

var subGroup = mx.Menu.getMainGroup('administration').getSubGroup('devices');
subGroup.addUrl('automover',100, 'url', '/automowerDevice/', '{i18n_Automower}', '{i18n_Robonect}', false);
subGroup.addUrl('inverter',200, 'url', 'https://{{pv_inverter_garage_ip}}', '{i18n_Inverter}', '{i18n_Solar (Extern)}', true);
subGroup.addUrl('printer',300, 'url', 'https://{{printer_ip}}', '{i18n_Laserprinter}', '{i18n_HPLaserJet}', true);
subGroup.addUrl('gateway',400, 'url', 'https://{{server_gateway}}', '{i18n_Router}', '{i18n_FritzBox}', true);
