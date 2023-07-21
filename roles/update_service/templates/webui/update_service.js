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
            if( data != null )
            {
                let msg = "";
                let json = JSON.parse(data);
                let job_is_running = json["job_is_running"];
                let needs_attention = json["needs_attention"];
                let needs_action = json["needs_action"];
                let available_system_uddates = json["system_updates"];
                let available_smartserver_changes = json["smartserver_changes"];

                if( job_is_running || needs_attention || needs_action || available_system_uddates > 0 || available_smartserver_changes > 0 )
                {
                    msg = mx.I18N.get("Updates","widget_system") + ": <strong>";

                    if( job_is_running ) msg += "<font class=\"icon-spin2 animate-spin\"></font>"

                    if( needs_action ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-red)\"></font>";
                    else if( needs_attention ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-yellow)\"></font>";

                    if( available_system_uddates > 0 || available_smartserver_changes > 0 )
                    {
                        msg += available_system_uddates + "/" + available_smartserver_changes;
                    }

                    msg +=  "</strong>";
                }

                ret.show(0,msg);
            }
            else
            {
                ret.alert(0,"Update Service: N/A");
            }

        }, mx.Core.encodeDict( { "type": "widget", "last_data_modified": null } ) );
    }
    return ret;
})( mx.Widgets.Object( "admin", [ { id: "availableUpdates", order: 50, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-update_system') } } ] ) );
{% endif %}
