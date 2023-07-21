mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_scanner', '/system_service/', 'admin', 212, '{i18n_Networkstructure}', '{i18n_Devices, Services & Structure}', "system_service_logo.svg", false);
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_wan', { "url": '//grafana.{host}/d/system-service-wan/system-service-wan', "callback": mx.Grafana.applyTheme }, 'admin', 212, '{i18n_WAN connection}', '{i18n_Speed & reachability}', "system_service_logo.svg", false);
{% if netflow_collector %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('system_service_netflow', { "url": '//grafana.{host}/d/system-service-netflow-overview/system-service-netflow-overview', "callback": mx.Grafana.applyTheme }, 'admin', 212, '{i18n_WAN traffic}', '{i18n_Netflow}', "system_service_logo.svg", false);

mx.Widgets.TrafficAlerts = (function( ret ) {
    let url = "/system_service/api/widget_state/";
    ret.refresh = function()
    {
        mx.Widgets.fetchContent("GET", url, function(data)
        {
            if( data != null )
            {
                let traffic = "";
                let json = JSON.parse(data);
                let wan_isp_state = json["wan_isp_state"];
                let wan_online_state = json["wan_online_state"];

                let msg = wan_online_state == "online" ? "<font class=\"icon-globe\"></font>" : "<font class=\"icon-globe\" style=\"color:var(--color-red)\"></font>";
                if( wan_isp_state == "fallback" ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-yellow)\"></font>";

                ret.show(0, mx.I18N.get("WAN","widget_system") + ": <strong>" + msg + "</strong>" );

                traffic += json["traffic_states"]["observed"] == 0 ? json["traffic_states"]["observed"] : "<font style=\"color:var(--color-green)\">" + json["traffic_states"]["observed"] + "</font>";
                traffic += "/";
                traffic += json["traffic_states"]["scanning"] == 0 ? json["traffic_states"]["scanning"] : "<font style=\"color:var(--color-yellow)\">" + json["traffic_states"]["scanning"] + "</font>";
                traffic += "/";
                traffic += json["traffic_states"]["intruded"] == 0 ? json["traffic_states"]["intruded"] : "<font style=\"color:var(--color-red)\">" + json["traffic_states"]["intruded"] + "</font>";
                ret.show(1, mx.I18N.get("Traffic","widget_system") + ": <strong>" + traffic + "</strong>");
            }
            else
            {
                ret.alert(0, "System Service: N/A");
                ret.alert(1, "");
            }
        } );
    }
    return ret;
})( mx.Widgets.Object( "admin", [ { id: "wanAlerts", order: 100, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-system_service_wan') } }, { id: "trafficAlerts", order: 102, click: function(event){ mx.Actions.openEntryById(event,'admin-system-system_service_netflow') } } ] ) );
{% endif %}
