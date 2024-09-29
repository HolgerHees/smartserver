mx.Nextcloud = (function( ret ) {
  ret.applyTheme = function(url)
  {
      js = "function init () {";
      if( mx.Page.isDarkTheme() )
      {
          js += "document.body.dataset.themes = 'dark';";
          js += "document.body.dataset.themeDefault = 'dark';";
          js += "document.body.dataset.themeDark = 'true';";
      }
      else
      {
          js += "document.body.dataset.themes = 'light';";
          js += "document.body.dataset.themeDefault = 'light';";
      }
      js += "}";
      js += "if(document.body){ init() } else { document.addEventListener('DOMContentLoaded', init);}";
      return { 'type': 'js', 'content': js };
  }
  return ret;
})( mx.Nextcloud || {} );

var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('nextcloud', { 'order': 100, 'title': '{i18n_Nextcloud}', 'icon': 'nextcloud_logo.svg' });
subGroup.addUrl('documents', ['user'], '//nextcloud.{host}/index.php/apps/files/', { 'order': 100, 'title': '{i18n_Files}', 'info': '{i18n_Documents}', 'icon': 'nextcloud_files.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
subGroup.addUrl('notes', ['user'], '//nextcloud.{host}/index.php/apps/notes/', { 'order': 110, 'title': '{i18n_Notes}', 'info': '{i18n_Note Infos}', 'icon': 'nextcloud_notes.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
subGroup.addUrl('deck', ['user'], '//nextcloud.{host}/index.php/apps/deck/', { 'order': 110, 'title': '{i18n_Tasks}', 'info': '{i18n_Deck}', 'icon': 'nextcloud_deck.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
subGroup.addUrl('photos', ['user'], '//nextcloud.{host}/index.php/apps/memories/', { 'order': 111, 'title': '{i18n_Photos}', 'info': '{i18n_Gallery}', 'icon': 'nextcloud_photos.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
subGroup.addUrl('news', ['user'], '//nextcloud.{host}/index.php/apps/news/', { 'order': 120, 'title': '{i18n_News}', 'info': '{i18n_RSSFeeds}', 'icon': 'nextcloud_news.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });
subGroup.addUrl('keeweb', ['user'], '//nextcloud.{host}/index.php/apps/keeweb/', { 'order': 130, 'title': '{i18n_Keys}', 'info': '{i18n_Passwords}', 'icon': 'nextcloud_passwords.svg', 'callbacks': { 'ping': mx.Nextcloud.applyTheme } });

