var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('weather', { 'order': 100, 'title': '{i18n_Weatherforecast}', 'icon': 'weather_service.svg' });
subGroup.addUrl(  'weather', ['user'], '/weather_service/detailOverview/', { 'order': 1000, 'title': '{i18n_Weatherforecast}', 'info': '{i18n_Meteo Group}', 'icon': 'weather_service.svg' });
mx.Widgets.CustomWeather = (function( widget ) {
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

    #customWeather svg {
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
    }
    #customWeather {
        overflow: visible !important;
    }`;

    let style = document.createElement('style');
    document.getElementsByTagName('head')[0].appendChild(style);
    style.type = 'text/css';
    style.appendChild(document.createTextNode(css));

    widget.processData = function(data)
    {
        if( data == null ) return widget.alert(0, "Weather N/A");

        let content = "";
        content += "<span style='display:inline-block;vertical-align: middle; padding-bottom: 4px;height:23px;width:23px;padding-left: 10px;padding-right: 15px;'>" + data["currentCloudsAsSVG"] + "</span>";
        content += "<span>" + data["currentAirTemperatureInCelsius"].toFixed(1) + "°C</span>";

        widget.show(0, content );
    }
    widget.click = function(event){
        mx.Actions.openEntryById(event, 'workspace-weather-weather');
    }
    return widget;
})( mx.Widgets.Object( "weather_service", "user", [ { id: "customWeather", order: 600, click: function(event){ mx.Widgets.CustomWeather.click(event); } } ] ) );
