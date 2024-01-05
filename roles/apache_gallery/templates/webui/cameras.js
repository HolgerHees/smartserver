var html = '<div class="service imageWatcher">';
{% for camera in camera_devices %}
html += '<div data-preview-interval="5000" data-fullscreen-interval="2000" data-name="{{camera['name']}}" data-src="/camera{{camera['proxy_identifier']}}Image" data-external-url="{{camera['external_url']}}" data-internal-menu="automation-cameras-{{camera['ftp_upload_name']}}"><img src="/main/img/loading.png"></div>';
{% endfor %}
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'device_camera.svg');
cameraSubGroup.addHtml('cameras', html, {"post": [ function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); } ] }, 'user', 100 );
{% for camera in camera_devices %}
cameraSubGroup.addUrl('{{camera['ftp_upload_name']}}','/gallery/?sub={{camera['ftp_upload_name']}}', 'user');
{% endfor %}

var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
{% for camera in camera_devices %}
subGroup.addUrl('{{camera['ftp_upload_name']}}', '{{camera['external_url']}}', 'admin', 310, '{i18n_Camera} {{camera['name']}}', '{{camera['details']}}', "device_camera.svg", true);
{% endfor %}
