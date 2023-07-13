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
            let json = JSON.parse(data);
            let wan_isp_state = json["wan_isp_state"];
            let wan_online_state = json["wan_online_state"];
            if( json["traffic_states"]["observed"] == undefined ) json["traffic_states"]["observed"] = 0;
            if( json["traffic_states"]["scanning"] == undefined ) json["traffic_states"]["scanning"] = 0;
            if( json["traffic_states"]["intruded"] == undefined ) json["traffic_states"]["intruded"] = 0;

            ret.getElement(0).innerHTML = mx.I18N.get("WAN","widget_system") + ": <strong>" + wan_online_state + " (" + wan_isp_state + ")</strong>";

            let traffic = "";
            traffic += json["traffic_states"]["observed"];
            traffic += "/";
            if( json["traffic_states"]["scanning"] > 0 ) traffic += "<font style=\"color:rgb(242, 204, 12)\">" + json["traffic_states"]["scanning"] + "</font>";
            else traffic += json["traffic_states"]["scanning"];
            traffic += "/";
            if( json["traffic_states"]["intruded"] > 0 ) traffic += "<font style=\"color:rgb(224, 47, 68)\">" + json["traffic_states"]["intruded"] + "</font>";
            else traffic += json["traffic_states"]["intruded"];

            ret.getElement(1).innerHTML = mx.I18N.get("Traffic","widget_system") + ": <strong>" + traffic + "</strong>";

            ret.show(0);
            ret.show(1);
        } );
    }
    return ret;
})( mx.Widgets.Object( "admin", [ { id: "wanAlerts", order: 300, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-system_service_wan') } }, { id: "trafficAlerts", order: 301, click: function(event){ mx.Actions.openEntryById(event,'admin-system-system_service_netflow') } } ] ) );
{% endif %}
