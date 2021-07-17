mx.Menu.getMainGroup('admin').getSubGroup('tools').addUrl('grafana_logs', '//grafana.{host}/d/logs/logs?autofitpanels','admin', 100, '{i18n_Server Logs}', '{i18n_Grafana}', false, 'grafana_logs.svg');
mx.Menu.getMainGroup('admin').getSubGroup('tools').addUrl('grafana_ui', '//grafana.{host}/','admin', 210, '{i18n_Grafana}', '{i18n_Dashboards}', false, 'grafana_logo.svg');
