var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}');

subGroup.addUrl('basicui',100, 'url', '//openhab.{host}/basicui/app', '{i18n_Control}', '{i18n_Basic UI}', false);
subGroup.addUrl('paperui',200, 'url', '//openhab.{host}/paperui/index.html', '{i18n_Administration}', '{i18n_Paper UI}', false);
subGroup.addUrl('habpanel',300, 'url', '//openhab.{host}/habpanel/index.html', '{i18n_Tablet UI}', '{i18n_HabPanel}', false);
subGroup.addUrl('habot',400, 'url', '//openhab.{host}/habot', '{i18n_Chatbot}', '{i18n_Habot}', false);
