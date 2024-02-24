{% if update_service_software_check_enabled %}mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_software', ['admin'], '/update_service/software/', { 'order': 310, 'title': '{i18n_Software}', 'info': '{i18n_Software status}', 'icon': 'update_software_logo.svg' });
{% endif %}
{% if update_service_system_check_enabled %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_system', ['admin'], '/update_service/system/', { 'order': 311, 'title': '{i18n_Updates}', 'info': '{i18n_System updates}', 'icon': 'update_system_logo.svg' });
mx.Widgets.AvailableUpdates = (function( widget ) {
    widget.processData = function(data)
    {
        if( data == null )
        {
            widget.alert(0, "Update Service N/A");
            return
        }

        let content = "";
        let is_running = data["is_running"];
        let needs_attention = data["needs_attention"];
        let needs_action = data["needs_action"];
        let available_system_uddates = data["system_updates"];
        let available_smartserver_changes = data["smartserver_changes"];

        if( is_running || needs_attention || needs_action || available_system_uddates > 0 || available_smartserver_changes > 0 )
        {
            content = mx.I18N.get("Updates","widget_system") + ": <strong>";

            if( is_running ) content += "<font class=\"icon-spin2 animate-spin\"></font>"

            if( needs_action ) content += "<font class=\"icon-attention\" style=\"color:var(--color-red)\"></font>";
            else if( needs_attention ) content += "<font class=\"icon-attention\" style=\"color:var(--color-yellow)\"></font>";

            if( available_system_uddates > 0 || available_smartserver_changes > 0 )
            {
                content += available_system_uddates + "/" + available_smartserver_changes;
            }

            content +=  "</strong>";
        }

        widget.show(0, content );
    }
    return widget;
})( mx.Widgets.Object( "update_service", "admin", [ { id: "availableUpdates", order: 50, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-update_system') } } ] ) );
{% endif %}
