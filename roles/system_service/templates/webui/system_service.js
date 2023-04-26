mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_scanner', '/system_service/', 'admin', 212, '{i18n_Networkstructure}', '{i18n_Devices, Services & Structure}', "system_service_logo.svg", false);
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_wan', { "url": '//grafana.{host}/d/system-service-wan/system-service-wan', "callback": mx.Grafana.applyTheme }, 'admin', 212, '{i18n_WAN connection}', '{i18n_Speed & reachability}', "system_service_logo.svg", false);
{% if netflow_collector %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_netflow', { "url": '//grafana.{host}/d/system-service-netflow-overview/system-service-netflow-overview', "callback": mx.Grafana.applyTheme }, 'admin', 212, '{i18n_WAN traffic}', '{i18n_Netflow}', "system_service_logo.svg", false);
{% endif %}
