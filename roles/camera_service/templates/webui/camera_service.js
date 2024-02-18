var html = '<div class="service imageWatcher">';
{% for camera in camera_devices %}
html += '<div data-preview-interval="5000" data-fullscreen-interval="2000" data-name="{{camera['name']}}" data-src="/camera{{camera['uid'] | capitalize}}Image" data-external-url="{{camera['external_url']}}"{% if 'ftp_upload_name' in camera %} data-internal-menu="automation-cameras-{{camera['uid']}}"{% endif %}><img></div>';
{% endfor %}
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', { 'order': 900, 'title': '{i18n_Cameras}', 'icon': 'device_camera.svg' });
cameraSubGroup.addHtml('cameras', ['user'], html, { 'order': 100, 'callbacks': {"init": [ function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); } ], "post": [ function(){ mx.ImageWatcher.post('.service.imageWatcher > div', 'cameras'); } ] }});
{% for camera in camera_devices %}{% if 'ftp_upload_name' in camera %}
cameraSubGroup.addUrl( '{{camera['uid']}}', ['user'], '/camera_service/?sub={{camera['ftp_upload_name']}}' );
{% endif %}{% endfor %}
