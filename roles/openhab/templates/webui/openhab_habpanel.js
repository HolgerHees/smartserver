var subGroup = mx.Menu.getMainGroup('automation').getSubGroup('openhab');

subGroup.addUrl('habpanel', ['admin'], '//openhab.{host}/habpanel/index.html', { 'order': 130, 'title': '{i18n_Tablet UI}', 'info': '{i18n_HabPanel}', 'icon': 'openhab_habpanel.svg' });
