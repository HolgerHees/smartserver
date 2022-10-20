mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_scanner', '/system_service/', 'admin', 112, '{i18n_Network}', '{i18n_Scanner}', "system_service_logo.svg", false);
{% if netflow_collector %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_netflow', { "url": '//grafana.{host}/d/system-service-netflow/system-service-netflow', "callback": mx.Grafana.applyTheme }, 'admin', 112, '{i18n_Internet Traffic}', '{i18n_Netflow}', "system_service_logo.svg", false);
{% endif %}
