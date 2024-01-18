var html = '<div class="service imageWatcher">';
{% for camera in camera_devices %}
html += '<div data-preview-interval="5000" data-fullscreen-interval="2000" data-name="{{camera['name']}}" data-src="/camera{{camera['uid'] | capitalize}}Image" data-external-url="{{camera['external_url']}}"{% if 'ftp_upload_name' in camera %} data-internal-menu="automation-cameras-{{camera['uid']}}"{% endif %}><img src="/main/img/loading.png"></div>';
{% endfor %}
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'device_camera.svg');
cameraSubGroup.addHtml('cameras', html, {"init": [ function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); } ], "post": [ function(){ mx.ImageWatcher.post('.service.imageWatcher > div', 'cameras'); } ] }, 'user', 100 );
{% for camera in camera_devices %}{% if 'ftp_upload_name' in camera %}
cameraSubGroup.addUrl('{{camera['uid']}}','/gallery/?sub={{camera['ftp_upload_name']}}', 'user');
{% endif %}{% endfor %}

/*var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
{% for camera in camera_devices %}
subGroup.addUrl('{{camera['uid']}}', '{{camera['external_url']}}', 'admin', 310, '{i18n_Camera} {{camera['name']}}', '{{camera['details']}}', "device_camera.svg", true);
{% endfor %}*/
