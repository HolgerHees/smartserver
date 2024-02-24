mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('ci', ['admin'], '/ci_service/', { 'order': 320, 'title': '{i18n_CI Service}', 'info': '{i18n_Continues Integration}', 'icon': 'ci_service_logo.svg' });
mx.Widgets.CiState = (function( widget ) {
    widget.processData = function(data)
    {
        if( data == null )
        {
            widget.alert(0, "CI Service N/A");
            return
        }

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
    return widget;
})( mx.Widgets.Object( "ci_service", "admin", [ { id: "ciState", order: 40, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-ci') } } ] ) );
