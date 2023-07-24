var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('weather', 100, '{i18n_Weatherforecast}', 'weather_service.svg');
subGroup.addUrl('weather', '/weather_service/detailOverview/', 'user', 1000, '{i18n_Weatherforecast}', '{i18n_Meteo Group}', 'weather_service.svg', false);

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
        --widget-value-color-weather-thunder: rgba(255, 165, 0, 0.9);
        --widget-value-color-weather-thunder-stroke: rgba(255, 165, 0, 0.9);
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

    var last_data_modified = null;
    var values = {};
    var content = "";

    ret.click = function(event){
        mx.Actions.openEntryById(event, 'workspace-weather-weather');
    }

    ret.refresh = function()
    {
        mx.Widgets.fetchContent("POST", "/weather_service/api/data/", function(data)
        {
            if( data != null )
            {
                let cloudData = JSON.parse(data)
                last_data_modified = cloudData["last_data_modified"];

                if( Object.keys(cloudData["changed_data"]).length > 0 )
                {
                    values = {...values, ...cloudData["changed_data"]};

                    content = "";
                    content += "<span style='display:inline-block;vertical-align: middle; padding-bottom: 4px;height:23px;width:23px;padding-left: 10px;padding-right: 15px;'>" + values["currentCloudsAsSVG"] + "</span>";
                    content += "<span>" + values["airTemperatureInCelsius"].toFixed(1) + "°C</span>";
                }

                ret.show(0, content );
            }
            else
            {
                ret.alert(0, "Weather N/A");
            }
        }, mx.Core.encodeDict( {"type": "widget", "fields": ["airTemperatureInCelsius","currentCloudsAsSVG"].join(","), "last_data_modified": last_data_modified } ) );
    }
    return ret;
})( mx.Widgets.Object( "user", [ { id: "customWeatcher", order: 600, click: function(event){ mx.Widgets.CustomWeather.click(event); } } ] ) );

