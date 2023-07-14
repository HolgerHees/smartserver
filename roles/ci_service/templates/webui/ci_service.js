mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('ci', '/ci_service/', 'admin', 320, '{i18n_CI Service}', '{i18n_Continues Integration}', "ci_service_logo.svg", false);
mx.Widgets.CiState = (function( ret ) {
    let url = "/ci_service/api/widget_state/"
    ret.refresh = function()
    {
        mx.Widgets.fetchContent("GET", url, function(data)
        {
            let json = JSON.parse(data);
            let msg = "";
            if( json["is_running"] || json["last_job_failed"] )
            {
                msg = mx.I18N.get("CI","widget_system") + ": <strong>";

                if( json["is_running"] ) msg += "<font class=\"icon-spin2 animate-spin\"></font>";
                if( json["last_job_failed"] ) msg += "<font class=\"icon-attention\" style=\"color:var(--color-red)\"></font>";

                msg += "</strong>";
            }
            ret.show(0, msg);
        } );
    }
    return ret;
})( mx.Widgets.Object( "admin", [ { id: "ciState", order: 40, click: function(event){ mx.Actions.openEntryById(event, 'admin-system-ci') } } ] ) );
