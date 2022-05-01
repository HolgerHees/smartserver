var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}', 'openhab_logo.svg');

subGroup.addUrl('basicui', '//openhab.{host}/basicui/app', 'user', 100, '{i18n_Homecontrol}', '{i18n_Basic UI}', false, 'openhab_basicui.svg');
subGroup.addUrl('habot', '//openhab.{host}/habot', 'user', 120, '{i18n_Chatbot}', '{i18n_Habot}', false, 'openhab_habot.svg');

subGroup.addUrl('mainui', '//openhab.{host}/', 'admin', 210, '{i18n_Administration}', '{i18n_Main UI}', false, 'openhab_adminui.svg');
subGroup.addUrl('metrics', { "url": '//grafana.{host}/d/openhab_metrics/openhab_metrics', "callback": mx.Grafana.applyTheme },'admin', 220, '{i18n_Metrics}', '{i18n_Grafana}', false, 'grafana_logs.svg');

