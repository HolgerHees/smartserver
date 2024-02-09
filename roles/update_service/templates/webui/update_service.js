{% if update_service_software_check_enabled %}mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_software', '/update_service/software/', 'admin', 310, '{i18n_Software}', '{i18n_Software status}', "update_software_logo.svg", false);
{% endif %}
{% if update_service_system_check_enabled %}
mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('update_system', '/update_service/system/', 'admin', 311, '{i18n_Updates}', '{i18n_System updates}', "update_system_logo.svg", false);
mx.Widgets.AvailableUpdates = (function( widget ) {
    let data = {}
    function processData(_data)
    {
        data = {...data, ..._data};

        let content = "";
        let job_is_running = data["job_status"]["job"] != null;
        let needs_attention = data["needs_attention"];
        let needs_action = data["needs_action"];
        let available_system_uddates = data["system_updates"];
        let available_smartserver_changes = data["smartserver_changes"];

        if( job_is_running || needs_attention || needs_action || available_system_uddates > 0 || available_smartserver_changes > 0 )
        {
            content = mx.I18N.get("Updates","widget_system") + ": <strong>";

            if( job_is_running ) content += "<font class=\"icon-spin2 animate-spin\"></font>"

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

    widget.init = function()
    {
        let socket = widget.getServiceSocket('update_service');
        socket.on("connect", () => socket.emit("join", "widget"));
        socket.on("data", (data) => processData( data ) );
        socket.on("error", (err) => widget.alert(0, "Update Service N/A") );
    }
    return widget;
})( mx.Widgets.Object( "admin", [ { id: "availableUpdates", order: 50, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-update_system') } } ] ) );
{% endif %}
