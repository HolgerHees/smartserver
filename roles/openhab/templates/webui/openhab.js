var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}', 'openhab_logo.svg');

subGroup.addUrl('basicui', '//openhab.{host}/basicui/app', 'user', 100, '{i18n_Homecontrol}', '{i18n_Basic UI}', 'openhab_basicui.svg', false);
subGroup.addUrl('habot', '//openhab.{host}/habot', 'user', 120, '{i18n_Chatbot}', '{i18n_Habot}', 'openhab_habot.svg', false);

subGroup.addUrl('mainui', '//openhab.{host}/', 'admin', 210, '{i18n_Administration}', '{i18n_Main UI}', 'openhab_adminui.svg', false);
subGroup.addUrl('metrics', { "url": '//grafana.{host}/d/openhab_metrics/openhab_metrics', "callback": mx.Grafana.applyTheme },'admin', 220, '{i18n_Metrics}', '{i18n_Grafana}', 'grafana_logs.svg', false);

