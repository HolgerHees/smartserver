var subGroup = mx.Menu.getMainGroup('automation').addSubGroup('openhab', 100, '{i18n_Openhab}', 'openhab_logo.svg');

subGroup.addUrl('basicui', '//openhab.{host}/basicui/app', 'user', 100, '{i18n_Homecontrol}', '{i18n_Basic UI}', 'openhab_basicui.svg', false);
subGroup.addUrl('habot', '//openhab.{host}/habot', 'user', 120, '{i18n_Chatbot}', '{i18n_Habot}', 'openhab_habot.svg', false);

subGroup.addUrl('mainui', '//openhab.{host}/', 'admin', 210, '{i18n_Administration}', '{i18n_Main UI}', 'openhab_adminui.svg', false);
subGroup.getEntry('mainui').disableLoadingGear();
subGroup.addUrl('metrics', { "url": '//grafana.{host}/d/openhab_metrics/openhab_metrics', "callback": mx.Grafana.applyTheme },'admin', 220, '{i18n_Metrics}', '{i18n_Grafana}', 'grafana_logs.svg', false);

{% if weather_data | length > 0 %}
mx.Widgets.CustomTemperatureUrl = {% if weather_data["openhab_temperature_item_url"] %}"//" + mx.Host.getAuthPrefix() + "openhab." + mx.Host.getDomain() + "{{ weather_data["openhab_temperature_item_url"] }}"{% else %}null{% endif %};
mx.Widgets.CustomCloudUrl = {% if weather_data["cloud_icon_url"] %}"//" + mx.Host.getAuthPrefix() + "openhab." + mx.Host.getDomain() + "{{ weather_data["cloud_icon_url"] }}"{% else %}null{% endif %};

mx.Widgets.CustomWeather = (function( ret ) {
    css = `:root {
        --widget-value-color-weather-sun: #ffdb26;
        --widget-value-color-weather-snowflake: white;

        --widget-value-color-weather-clouds: white;
        --widget-value-color-weather-raindrop: white;
        --widget-value-color-weather-thunder: rgba(255, 165, 0, 0.8);
        --widget-value-color-weather-thunder-stroke: rgba(255, 165, 0, 0.8);
    }

    :root body.dark {
        --widget-value-color-weather-clouds: white;
        --widget-value-color-weather-raindrop: #4b86c8;
        --widget-value-color-weather-thunder: rgba(255, 165, 0, 0.6);
        --widget-value-color-weather-thunder-stroke: rgba(255, 165, 0, 0.6);
    }

    #customWeatcher svg {
        --svg-weather-clouds-stroke: var(--widget-value-color-weather-clouds);
        --svg-weather-clouds-stroke-width: 3px;
        --svg-weather-clouds-fill: transparent;
        --svg-weather-sun-stroke: var(--widget-value-color-weather-sun);
        --svg-weather-sun-stroke-width: 2px;
        --svg-weather-sun-fill: var(--widget-value-color-weather-sun);
        --svg-weather-moon-stroke: var(--widget-value-color-weather-clouds);
        --svg-weather-moon-stroke-width: 1px;
        --svg-weather-moon-fill: transparent;
        --svg-weather-stars-stroke: var(--widget-value-color-weather-clouds);
        --svg-weather-stars-stroke-width: 0.5px;
        --svg-weather-stars-fill: transparent;
        --svg-weather-thunder-stroke: var(--widget-value-color-weather-thunder-stroke);
        --svg-weather-thunder-stroke-width: 1px;
        --svg-weather-thunder-fill: var(--widget-value-color-weather-thunder);
        --svg-weather-raindrop-stroke: var(--widget-value-color-weather-clouds);
        --svg-weather-raindrop-stroke-width: 5px;
        --svg-weather-raindrop-fill: var(--widget-value-color-weather-raindrop);
        --svg-weather-snowflake-stroke: var(--widget-value-color-weather-clouds);
        --svg-weather-snowflake-stroke-width: 1px;
        --svg-weather-snowflake-fill: var(--widget-value-color-weather-snowflake);
        /*--svg-weather-mask-fill: white;*/

        margin: -10px;
    }`;

    let style = document.createElement('style');
    document.getElementsByTagName('head')[0].appendChild(style);
    style.type = 'text/css';
    style.appendChild(document.createTextNode(css));


    let temperatureData = null;
    let cloudLastHour = null;
    let cloudData = null;

    ret.click = function(event){
        if( mx.Menu.checkMenu("workspace", "weather", "weather") ) mx.Actions.openEntryById(event, 'workspace-weather-weather');
        else mx.Actions.openEntryById(event, 'automation-openhab-basicui');
    }

    ret.refresh = function()
    {
        temperatureData = null;
        const d = new Date();
        let currentHour = d.getHours();
        if( cloudLastHour != currentHour )
        {
            cloudLastHour= currentHour;
            cloudData = null;
        }

        function setContent()
        {
            if( !temperatureData || !cloudData )
            {
                return;
            }

            ret.show(0, "<span style='display:inline-block;vertical-align: middle; padding-bottom: 4px;height:23px;width:23px;padding-left: 10px;padding-right: 15px;'>" + cloudData + "</span><strong>" + temperatureData["state"] + "°C</strong>" );
        }

        if( cloudData == null && mx.Widgets.CustomCloudUrl != null)
        {
            mx.Widgets.fetchContent("GET", mx.Widgets.CustomCloudUrl, function(data)
            {
                cloudData = data;
                setContent();
            } );
        }
        if( temperatureData == null && mx.Widgets.CustomTemperatureUrl != null)
        {
            mx.Widgets.fetchContent("GET", mx.Widgets.CustomTemperatureUrl, function(data)
            {
                temperatureData = JSON.parse(data);
                setContent();
            } );
        }
    }
    return ret;
})( mx.Widgets.Object( "user", [ { id: "customWeatcher", order: 600, click: function(event){ mx.Widgets.CustomWeather.click(event); } } ] ) );
{% endif %}
