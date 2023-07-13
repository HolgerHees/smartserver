var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}', 'openhab_logo.svg');

subGroup.addUrl('basicui', '//openhab.{host}/basicui/app', 'user', 100, '{i18n_Homecontrol}', '{i18n_Basic UI}', 'openhab_basicui.svg', false);
subGroup.addUrl('habot', '//openhab.{host}/habot', 'user', 120, '{i18n_Chatbot}', '{i18n_Habot}', 'openhab_habot.svg', false);

subGroup.addUrl('mainui', '//openhab.{host}/', 'admin', 210, '{i18n_Administration}', '{i18n_Main UI}', 'openhab_adminui.svg', false);
subGroup.getEntry('mainui').disableLoadingGear();
subGroup.addUrl('metrics', { "url": '//grafana.{host}/d/openhab_metrics/openhab_metrics', "callback": mx.Grafana.applyTheme },'admin', 220, '{i18n_Metrics}', '{i18n_Grafana}', 'grafana_logs.svg', false);

{% if openhab_garden_temperature_item %}
mx.Widgets.CustomTemperature = (function( ret ) {
    let url = "//" + mx.Host.getAuthPrefix() + "openhab." + mx.Host.getDomain() + "/rest/items/{{ openhab_garden_temperature_item }}"
    ret.refresh = function()
    {
        mx.Widgets.fetchContent("GET", url, function(data)
        {
            let json = JSON.parse(data);

            ret.getElement(0).innerHTML = mx.I18N.get("Temperature","widget_openhab") + ": <strong>" + json["state"] + "°C</strong>";
            ret.show(0);
        } );
    }
    return ret;
})( mx.Widgets.Object( "user", [ { id: "customTemperature", order: 600, click: function(event){ mx.Actions.openEntryById(event, 'automation-openhab-basicui') } } ] ) );
{% endif %}
