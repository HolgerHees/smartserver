var html = '<div class="service imageWatcher">';
html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation-cameras-camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
cameraSubGroup.addHtml('cameras', html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); }, 'user', 100 );
cameraSubGroup.addUrl('camera_streedside','/gallery/?sub=camera', 'user');

var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('automover', '/automowerDevice/', 'admin', 110, '{i18n_Automower}', '{i18n_Robonect}', "proxy_mower.svg", false);
subGroup.addUrl('inverter', 'https://{{pv_inverter_garage_ip}}', 'admin', 120, '{i18n_Inverter}', '{i18n_Solar (Extern)}', "proxy_solar.svg", true);
subGroup.addUrl('printer', 'https://{{printer_ip}}', 'user', 210, '{i18n_Laserprinter}', '{i18n_HPLaserJet}', "proxy_printer.svg", true);
subGroup.addUrl('gateway', 'https://{{server_gateway}}', 'admin', 220, '{i18n_Router}', '{i18n_FritzBox}', "proxy_router.svg", true);
subGroup.addUrl('camera', 'http://{{camera_streedside_ip}}', 'admin', 310, '{i18n_Camera}', '{i18n_Streedside}', "proxy_camera.svg", true);
