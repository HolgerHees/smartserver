var mainGroup = mx.Menu.addMainGroup('nextcloud', 1000, '{i18n_Nextcloud}');
var subGroup = mainGroup.addSubGroup('nextcloud', 100, '{i18n_Nextcloud}','nextcloud_logo.svg');
subGroup.addUrl('documents',100, 'user', '//nextcloud.{host}/', '{i18n_Documents}', '', false, 'files.svg');
subGroup.addUrl('news',200, 'user', '//nextcloud.{host}/index.php/apps/news/', '{i18n_News}', '', false);
subGroup.addUrl('keeweb',300, 'user', '//nextcloud.{host}/index.php/apps/keeweb/', '{i18n_Keys}', '{i18n_Keeweb}', false);
