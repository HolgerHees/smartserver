var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}', 'openhab_logo.svg');

subGroup.addUrl('basicui', '//openhab.{host}/basicui/app', 'user', 100, '{i18n_Control}', '{i18n_Basic UI}', false);
subGroup.addUrl('paperui', '//openhab.{host}/paperui/index.html', 'admin', 200, '{i18n_Administration}', '{i18n_Paper UI}', false);
subGroup.addUrl('habot', '//openhab.{host}/habot', 'user', 300, '{i18n_Chatbot}', '{i18n_Habot}', false);
