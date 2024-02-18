mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('ci', ['admin'], '/ci_service/', { 'order': 320, 'title': '{i18n_CI Service}', 'info': '{i18n_Continues Integration}', 'icon': 'ci_service_logo.svg' });
mx.Widgets.CiState = (function( widget ) {
    let data = {}
    function processData(_data)
    {
        data = {...data, ..._data};

        let msg = "";
        if( data["is_running"] || data["last_job_failed"] )
        {
            msg = mx.I18N.get("CI","widget_system") + ": <strong>";

            if( data["is_running"] ) msg += "<font class=\"icon-spin2 animate-spin\"></font>";
            if( data["last_job_failed"] ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-red)\"></font>";

            msg += "</strong>";
        }
        widget.show(0, msg);
    }

    widget.init = function()
    {
        let socket = widget.getServiceSocket('ci_service');
        socket.on("connect", () => socket.emit("join", "widget"));
        socket.on("data", (data) => processData( data ) );
        socket.on("error", (err) => widget.alert(0, "CI Service") );
    }
    return widget;
})( mx.Widgets.Object( "admin", [ { id: "ciState", order: 40, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-ci') } } ] ) );
