var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('nextcloud', 100, '{i18n_Nextcloud}','nextcloud_logo.svg');
subGroup.addUrl('documents','//nextcloud.{host}/index.php/apps/files/', ['user'], 100, '{i18n_Files}', '{i18n_Documents}', 'nextcloud_files.svg', false);
subGroup.addUrl('collectives','//nextcloud.{host}/index.php/apps/collectives/', ['user'], 110, '{i18n_Notes}', '{i18n_Note Infos}', 'nextcloud_notes.svg', false);
subGroup.addUrl('deck','//nextcloud.{host}/index.php/apps/deck/', ['user'], 110, '{i18n_Tasks}', '{i18n_Deck}', 'nextcloud_deck.svg', false);
subGroup.addUrl('photos','//nextcloud.{host}/index.php/apps/photos/', ['user'], 111, '{i18n_Photos}', '{i18n_Gallery}', 'nextcloud_photos.svg', false);
subGroup.addUrl('news','//nextcloud.{host}/index.php/apps/news/', ['user'], 120, '{i18n_News}', '{i18n_RSSFeeds}', 'nextcloud_news.svg', false);
subGroup.addUrl('keeweb','//nextcloud.{host}/index.php/apps/keeweb/', ['user'], 130, '{i18n_Keys}', '{i18n_Keeweb}', 'nextcloud_keeweb.svg', false);

