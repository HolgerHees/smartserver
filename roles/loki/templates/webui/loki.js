mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('grafana_logs', ['admin'], '//grafana.{host}/explore?left={"datasource":"Loki","queries":[{"refId":"A","expr":"{level%3D~\\\"ERROR|WARN\\\"}","queryType":"range"}],"range":{"from":"now-24h","to":"now"}}', { 'order': 100, 'callback': mx.Grafana.applyTheme, 'title': '{i18n_Server Logs}', 'info': '{i18n_Grafana}', 'icon': 'grafana_logs.svg' });
