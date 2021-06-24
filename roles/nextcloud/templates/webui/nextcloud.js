var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('nextcloud', 100, '{i18n_Nextcloud}','nextcloud_logo.svg');
subGroup.addUrl('documents','//nextcloud.{host}/index.php/apps/files/', ['user','nextcloudadmin'], 100, '{i18n_Files}', '{i18n_Documents}', false, 'nextcloud_files.svg');
//subGroup.addUrl('photos','//nextcloud.{host}/index.php/apps/photos/', ['user','nextcloudadmin'], 110, '{i18n_Photos}', '{i18n_Gallery}', false, 'nextcloud_photos.svg');
subGroup.addUrl('news','//nextcloud.{host}/index.php/apps/news/', ['user','nextcloudadmin'], 120, '{i18n_News}', '{i18n_RSSFeeds}', false, 'nextcloud_news.svg');
subGroup.addUrl('keeweb','//nextcloud.{host}/index.php/apps/keeweb/', ['user','nextcloudadmin'], 130, '{i18n_Keys}', '{i18n_Keeweb}', false, 'nextcloud_keeweb.svg');
