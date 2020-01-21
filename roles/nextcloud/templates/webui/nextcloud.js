var mainGroup = mx.Menu.addMainGroup('nextcloud', 1000, '{i18n_Nextcloud}');
var subGroup = mainGroup.addSubGroup('nextcloud', 100, '{i18n_Nextcloud}');
subGroup.addUrl(100, 'url', '//nextcloud.{host}/', '{i18n_Documents}', '', false);
subGroup.addUrl(200, 'url', '//nextcloud.{host}/index.php/apps/news/', '{i18n_News}', '', false);
subGroup.addUrl(300, 'url', '//nextcloud.{host}/index.php/apps/keeweb/', '{i18n_Keys}', '{i18n_Keeweb}', true);
