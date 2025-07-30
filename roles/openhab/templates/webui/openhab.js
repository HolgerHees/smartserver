mx.OpenHAB = (function( ret ) {
    ret.applyTheme = function(url)
    {
        var css = `header, header > * { max-height: 56px !important; min-height: 56px !important; }`;
        if( mx.Page.isDarkTheme() ) css += `body { --body-bg: #202124 !important; --header-bg: rgba(25,118,210,0.3) !important; }`;
        else css += `body { --body-bg: white !important; --header-bg: #1976D2 !important; }`;
        return { 'type': 'css', 'content': css };
    }
    return ret;
})( mx.OpenHAB || {} );

var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', { 'order': 100, 'title': '{i18n_Openhab}', 'icon': 'openhab_logo.svg' });

subGroup.addUrl('basicui', ['user'], '//openhab.{host}/basicui/app', { 'order': 100, 'title': '{i18n_Homecontrol}', 'info': '{i18n_Basic UI}', 'icon': 'openhab_basicui.svg', 'callbacks': { 'ping': mx.OpenHAB.applyTheme } });
subGroup.addUrl('habot', ['user'], '//openhab.{host}/habot', { 'order': 120, 'title': '{i18n_Chatbot}', 'info': '{i18n_Habot}', 'icon': 'openhab_habot.svg' });

subGroup.addUrl('mainui', ['user'], '//openhab.{host}/', { 'order': 210, 'title': '{i18n_Administration}', 'info': '{i18n_Main UI}', 'icon': 'openhab_adminui.svg' });
{% if grafana_enabled %}
subGroup.addUrl('metrics', ['admin'], '//grafana.{host}/d/openhab_metrics/openhab_metrics', { 'order': 220, 'title': '{i18n_Metrics}', 'info': '{i18n_Grafana}', 'icon': 'grafana_logs.svg', 'callbacks': { 'url': mx.Grafana.applyTheme } });
{% endif %}
