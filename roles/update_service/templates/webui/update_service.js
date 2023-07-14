{% if update_service_software_check_enabled %}mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_software', '/update_service/software/', 'admin', 310, '{i18n_Software}', '{i18n_Software status}', "update_software_logo.svg", false);
{% endif %}
{% if update_service_system_check_enabled %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_system', '/update_service/system/', 'admin', 311, '{i18n_Updates}', '{i18n_System updates}', "update_system_logo.svg", false);
mx.Widgets.AvailableUpdates = (function( ret ) {
    let url = "/update_service/api/state/";
    ret.refresh = function()
    {
        mx.Widgets.fetchContent("POST", url, function(data)
        {
            let json = JSON.parse(data);
            let job_is_running = json["job_is_running"];
            let available_system_uddates = json["system_updates"];
            let available_smartserver_changes = json["smartserver_changes"];

            let msg = "";

            if( job_is_running || available_system_uddates > 0 || available_smartserver_changes > 0 )
            {
                msg = mx.I18N.get("Updates","widget_system") + ": <strong>";

                if( job_is_running )
                {
                    msg += "<font class=\"icon-spin2 animate-spin\"></font>"
                }
                if( available_system_uddates > 0 || available_smartserver_changes > 0 )
                {
                    msg += available_system_uddates + "/" + available_smartserver_changes;
                }

                msg +=  "</strong>";
            }

            ret.show(0,msg);

        }, mx.Core.encodeDict( { "type": "widget", "last_data_modified": null } ) );
    }
    return ret;
})( mx.Widgets.Object( "admin", [ { id: "availableUpdates", order: 50, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-update_system') } } ] ) );
{% endif %}
