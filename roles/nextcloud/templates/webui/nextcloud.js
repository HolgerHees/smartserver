var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('nextcloud', 100, '{i18n_Nextcloud}','nextcloud_logo.svg');
subGroup.addUrl('documents','//nextcloud.{host}/index.php/apps/files/', ['user','nextcloudadmin'], 100, '{i18n_Documents}', '', false, 'files.svg');
subGroup.addUrl('news','//nextcloud.{host}/index.php/apps/news/', ['user','nextcloudadmin'], 200, '{i18n_News}', '', false);
subGroup.addUrl('keeweb','//nextcloud.{host}/index.php/apps/keeweb/', ['user','nextcloudadmin'], 300, '{i18n_Keys}', '{i18n_Keeweb}', false);
