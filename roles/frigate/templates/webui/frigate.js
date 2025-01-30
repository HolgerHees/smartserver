var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras_neu', { 'order': 900, 'title': '{i18n_Cameras}', 'icon': 'device_camera.svg' });
cameraSubGroup.addUrl('cameras_frigate',  ['admin'], '//frigate.{host}/', { 'order': 100, 'title': 'CO2 {i18n_Cameras}', 'info': '{i18n_Frigate NVR}', 'icon': 'device_camera.svg' });
