var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('nextcloud', { 'order': 100, 'title': '{i18n_Nextcloud}', 'icon': 'nextcloud_logo.svg' });
subGroup.addUrl('documents', ['user'], '//nextcloud.{host}/index.php/apps/files/', { 'order': 100, 'title': '{i18n_Files}', 'info': '{i18n_Documents}', 'icon': 'nextcloud_files.svg' });
subGroup.addUrl('notes', ['user'], '//nextcloud.{host}/index.php/apps/notes/', { 'order': 110, 'title': '{i18n_Notes}', 'info': '{i18n_Note Infos}', 'icon': 'nextcloud_notes.svg' });
subGroup.addUrl('deck', ['user'], '//nextcloud.{host}/index.php/apps/deck/', { 'order': 110, 'title': '{i18n_Tasks}', 'info': '{i18n_Deck}', 'icon': 'nextcloud_deck.svg' });
subGroup.addUrl('photos', ['user'], '//nextcloud.{host}/index.php/apps/photos/', { 'order': 111, 'title': '{i18n_Photos}', 'info': '{i18n_Gallery}', 'icon': 'nextcloud_photos.svg' });
subGroup.addUrl('news', ['user'], '//nextcloud.{host}/index.php/apps/news/', { 'order': 120, 'title': '{i18n_News}', 'info': '{i18n_RSSFeeds}', 'icon': 'nextcloud_news.svg' });
subGroup.addUrl('keeweb', ['user'], '//nextcloud.{host}/index.php/apps/keeweb/', { 'order': 130, 'title': '{i18n_Keys}', 'info': '{i18n_Passwords}', 'icon': 'nextcloud_passwords.svg' });

