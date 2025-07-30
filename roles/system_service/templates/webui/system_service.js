{% if grafana_enabled %}
mx.SystemService = (function( ret ) {
  ret.grafanaListener = function(url)
  {
      js = "window.addEventListener(\"message\", function(event){ "
      js += "  if( typeof event.data != 'object' || !event.data['type'] || ![ 'grafana' ].includes(event.data['type']) ) return;";
      js += "  if( event.data['content'] == \"reload\" ) window.document.querySelector(\"div.refresh-picker button\").click();";
      js += "});";
      return { 'type': 'js', 'content': js };
  }
  return ret;
})( mx.SystemService || {} );
{% endif %}

mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_scanner', ['admin'], '/system_service/', { 'order': 212, 'title': '{i18n_Networkstructure}', 'info': '{i18n_Devices, Services & Structure}', 'icon': 'system_service_logo.svg' });
{% if grafana_enabled %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_wan', ['admin'], '//grafana.{host}/d/system-service-wan/system-service-wan', { 'order': 212, 'title': '{i18n_WAN connection}', 'info': '{i18n_Speed & reachability}', 'icon': 'system_service_logo.svg', 'callbacks': { 'url': mx.Grafana.applyTheme, 'ping': mx.SystemService.grafanaListener } });
{% if system_service_netflow_collector_enabled %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_netflow', ['admin'], '//grafana.{host}/d/system-service-netflow-overview/system-service-netflow-overview', { 'order': 212, 'title': '{i18n_WAN traffic}', 'info': '{i18n_Netflow}', 'icon': 'system_service_logo.svg', 'callbacks': { 'url': mx.Grafana.applyTheme } });
mx.Widgets.TrafficAlerts = (function( widget ) {
    widget.processData = function(data)
    {
        if( data == null )
        {
            widget.alert(0, "System Service N/A");
            widget.alert(1, "");
            return
        }

        let traffic = "";
        let wan_isp_state = data["wan_isp_state"];
        let wan_online_state = data["wan_online_state"];

        let msg = wan_online_state == "online" ? "<font class=\"icon-globe\"></font>" : "<font class=\"icon-globe\" style=\"color:var(--color-red)\"></font>";
        if( wan_isp_state == "fallback" ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-yellow)\"></font>";

        widget.show(0, mx.I18N.get("WAN","widget_system") + ": <strong>" + msg + "</strong>" );

        traffic += data["traffic_states"]["observed"] == 0 ? data["traffic_states"]["observed"] : "<font style=\"color:var(--color-green)\">" + data["traffic_states"]["observed"] + "</font>";
        traffic += "/";
        traffic += data["traffic_states"]["scanning"] == 0 ? data["traffic_states"]["scanning"] : "<font style=\"color:var(--color-yellow)\">" + data["traffic_states"]["scanning"] + "</font>";
        traffic += "/";
        traffic += data["traffic_states"]["intruded"] == 0 ? data["traffic_states"]["intruded"] : "<font style=\"color:var(--color-red)\">" + data["traffic_states"]["intruded"] + "</font>";

        blocked = data["blocked_traffic"] > 0 ? " <font class=\"icon-block\"></font><strong>" + data["blocked_traffic"] + "</strong>" : "";

        widget.show(1, mx.I18N.get("Traffic","widget_system") + ": <strong>" + traffic + "</strong>" + blocked);
    }
    return widget;
})( mx.Widgets.Object( "system_service", "admin", [ { id: "wanAlerts", order: 100, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-system_service_wan') } }, { id: "trafficAlerts", order: 102, click: function(event){
    let entry = mx.Menu.getMainGroup('admin').getSubGroup('system').getEntry('system_service_netflow');
    mx.Actions.openEntry(entry, entry.getUrl() + "?var-Filters=group|!%3D|normal" );
    //mx.Actions.openEntryById(event,'admin-system-system_service_netflow')
} } ] ) );
{% endif %}
{% endif %}
