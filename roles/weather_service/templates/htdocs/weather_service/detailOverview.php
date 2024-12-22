<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

function getSVG( $icon, $id)
{
    return str_replace("\n", "", file_get_contents('icons/svg/' . $id . '.svg') );
}
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/weather_service/"]); ?>
<script>
mx.WeatherCore = (function( ret ) {
    ret.socket = null;
    ret.active_day = null;
    var data = {};

    function buildRow(id, time, cloud, maxTemperature, minTemperature, sunshineDuration, precipitationProbability, precipitationAmount, windSpeed, windDirection, clickDate)
    {
        let row = '<div id="' + id + '" class="hour';
        if( clickDate ) row += ' mvClickable" mv-date="' + clickDate + '"';
        else row += '"';
        row += '>';
        row += '<div class="time">' + time + '</div>';
        row += '<div class="cloud">' + cloud + '</div>';
        row += '<div class="temperature"><div><div class="main"><span class="max">' + mx.WeatherHelper.formatNumber(maxTemperature) + '</span><span class="min">' + mx.WeatherHelper.formatNumber(minTemperature) + '</span></div><div class="sub">°C</div></div></div>';
        row += '<div class="info">';
        row += '  <div class="sunshineDuration"><div class="sun icon"><?php echo str_replace("'", "\\'", getSVG('sun', 'sun_grayscaled') ); ?></div><div>' + mx.WeatherHelper.formatDuration( sunshineDuration ) + '</div></div>';
        row += '  <div class="precipitationProbability"><div class=\"icon\"><?php echo str_replace("'", "\\'", getSVG('rain','rain_grayscaled') ); ?></div><div>' + precipitationProbability + ' %</div></div>';
        row += '  <div class="precipitationAmount"><div></div><div>' + mx.WeatherHelper.formatNumber( precipitationAmount ) + ' mm</div></div>';
        row += '</div>';
        row += '<div class="wind"><div>';
        row += '  <div>' + mx.WeatherHelper.formatNumber( windSpeed ) + ' km/h</div>';
        row += '  <div class="compass">'
        row += '    <div class="circle"><?php echo str_replace("'", "\\'", getSVG('compass_circle', 'compass_circle_grayscaled') ); ?></div>';
        row += '    <div class="needle" style="transform: rotate(' + ( windDirection - 180 ) + 'deg)"><?php echo str_replace("'", "\\'", getSVG('compass_needle', 'compass_needle_grayscaled') ); ?></div>';
        row += '  </div>';
        row += '</div></div>';
        if( clickDate ) row += '<div class="status"></div>';
        row += '</div>';

        return row;
    }

    function initButtons()
    {
        var weekButton = document.getElementById("weekButton");
        weekButton.addEventListener("click",function(){
            var todayHeadline = document.querySelector(".forecast .today .headline");

            var weekList = document.querySelector(".forecast .week");
            weekList.style.top = mx.Core.getOffsets(todayHeadline)["top"] + "px";

            if( weekList.classList.contains("open") )
            {
              weekButton.innerHTML = mx.I18N.get("Week");
              weekButton.classList.remove("open");
              weekList.classList.remove("open");
              window.setTimeout(function(){
                if( !weekButton.classList.contains("open") )
                {
                  weekButton.style.zIndex = "";
                  weekButton.classList.remove("animated");
                }
              },300);
            }
            else
            {
              weekButton.classList.add("animated");
              window.setTimeout(function(){
                weekButton.innerHTML = mx.I18N.get("Close");
                weekButton.style.zIndex = "101";
                weekButton.classList.add("open");
                weekList.classList.add("open");
              },0);
            }
        });

        // LOCATION => 52.3476672,13.6215805 lat / long
        // target => 1516323.13/6863234.61

        var rainButton = document.querySelector("#rainButton");
        var rainFrame = document.querySelector("#rainFrame iframe");
        rainFrame.src="about:blank";
        rainButton.addEventListener("click",function(){
            var url = "https://embed.windy.com/embed2.html?lat=52.344&lon=13.618&detailLat=52.316&detailLon=13.392&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
            //window.open(url);
            if( rainFrame.parentNode.classList.contains("open") )
            {
              rainButton.classList.remove("open");
              rainButton.innerHTML = mx.I18N.get("Radar");
              rainFrame.parentNode.classList.remove("open");
              rainFrame.src="";
              window.setTimeout(function(){
                if( !weekButton.classList.contains("open") )
                {
                  rainButton.style.zIndex = "";
                  rainButton.classList.remove("animated");
                }
              },300);
            }
            else
            {
              rainButton.classList.add("animated");
              window.setTimeout(function(){
                rainButton.innerHTML = mx.I18N.get("Close");
                rainButton.style.zIndex = "101";
                rainButton.classList.add("open");
                rainFrame.parentNode.classList.add("open");
                rainFrame.src=url;
              },0);
            }
        });
    }

    function refreshWeek(day)
    {
        mx.WeatherCore.socket.emit('getWeekData', day);
    }

    ret.processData = function(changed_data)
    {
        data = {...data, ...changed_data};

        if( "currentAirTemperatureInCelsius" in changed_data) mx.$(".current .summary .temperature .value").innerHTML = mx.WeatherHelper.formatNumber(data["currentAirTemperatureInCelsius"]) + ' °C';
        if( "currentPerceivedTemperatureInCelsius" in changed_data) mx.$(".current .summary .perceived .value").innerHTML = mx.WeatherHelper.formatNumber(data["currentPerceivedTemperatureInCelsius"]) + ' °C';

        if( "currentWindSpeedInKilometerPerHour" in changed_data || "currentWindSpeedInKilometerPerHour" in changed_data )
        {
            let windSpeed = mx.WeatherHelper.formatNumber(data["currentWindSpeedInKilometerPerHour"]);
            let windGust = mx.WeatherHelper.formatNumber(data["currentWindGustInKilometerPerHour"]);
            let wind = windSpeed;
            if( windSpeed != windGust && data["currentWindGustInKilometerPerHour"] > 0 )
            {
                wind += ' (' + windGust + ')';
            }
            mx.$(".current .summary .wind .value").innerHTML = wind + ' km/h';
        }

        if( "currentRainRateInMillimeterPerHour" in changed_data || "currentRainDailyInMillimeter" in changed_data )
        {
            let rainValue = mx.WeatherHelper.formatNumber(data["currentRainRateInMillimeterPerHour"]);
            let rainDaily = mx.WeatherHelper.formatNumber(data["currentRainDailyInMillimeter"]);
            let rain = rainValue
            if( rainValue != rainDaily && data["currentRainDailyInMillimeter"] > 0 )
            {
                rain += ' (' + rainDaily + ')';
            }
            mx.$(".current .summary .rain .value").innerHTML = rain + ' mm';
        }

        if( "currentCloudsAsSVG" in changed_data) mx.$(".current .cloud").innerHTML = mx.WeatherHelper.formatNumber(data["currentCloudsAsSVG"]);

        if( "currentUvIndex" in changed_data) mx.$(".current .uv .value").innerHTML = mx.WeatherHelper.formatNumber(data["currentUvIndex"]);

        if( "astroSunrise" in changed_data)
        {
            let sunrise = new Date();
            sunrise.setTime(Date.parse(data["astroSunrise"]));
            mx.$(".current .sunrise .value").innerHTML = mx.WeatherHelper.formatHour(sunrise);
        }
        if( "astroSunset" in changed_data)
        {
            let sunset = new Date();
            sunset.setTime(Date.parse(data["astroSunset"]));
            mx.$(".current .sunset .value").innerHTML = mx.WeatherHelper.formatHour(sunset);
        }

        if( "dayActive" in changed_data )
        {
            if( data["dayActive"] )
            {
                mx.WeatherCore.active_day = new Date();
                mx.WeatherCore.active_day.setTime(Date.parse(data["dayActive"]));
                mx.$(".today .title").innerHTML = mx.WeatherHelper.formatDay(mx.WeatherCore.active_day);
            }
            else
            {
                mx.WeatherCore.active_day = null;
                mx.$(".today .title").innerHTML = "";
            }
        }

        let now = new Date();

        if( "dayList" in changed_data)
        {
            mx.$(".today .summary .temperature .value span.min").innerHTML = mx.WeatherHelper.formatNumber(data["dayMinTemperature"]);
            mx.$(".today .summary .temperature .value span.max").innerHTML = mx.WeatherHelper.formatNumber(data["dayMaxTemperature"]);
            mx.$(".today .summary .wind .value span").innerHTML = mx.WeatherHelper.formatNumber(data["dayMaxWindSpeed"]);
            mx.$(".today .summary .rain .value span").innerHTML = mx.WeatherHelper.formatNumber(data["daySumRain"]);
            mx.$(".today .summary .sun .value span").innerHTML = mx.WeatherHelper.formatDuration(data["daySumSunshine"]);

            let html_rows = [];
            let active_id = null;
            data["dayList"].forEach(function(row)
            {
                let start = new Date();
                start.setTime(Date.parse(row["start"]));
                let end = new Date();
                end.setTime(Date.parse(row["end"]));

                let id = "day_" + start.getTime();
                if( now.getTime() >= start.getTime() && now.getTime() <=  end.getTime() ) active_id = id;

                let time = '<div class="from">' + mx.WeatherHelper.formatHour(start) + '</div>';
                let html_row = buildRow(
                    id,
                    time,
                    row["svg"],
                    row["maxAirTemperatureInCelsius"],
                    row["minAirTemperatureInCelsius"],
                    row["sunshineDurationInMinutes"],
                    row["precipitationProbabilityInPercent"],
                    row["precipitationAmountInMillimeter"],
                    row["windSpeedInKilometerPerHour"],
                    row["windDirectionInDegree"],
                    null
                );
                html_rows.push(html_row);
            });

            mx.$(".today .hours").innerHTML = html_rows.length > 0 ? html_rows.join("") : mx.I18N.get("No forecasts available");
            if( active_id ) mx.$("#" + active_id ).classList.add("active");
        }

        if( "weekList" in changed_data)
        {
            mx.$(".week .summary .temperature .value span.min").innerHTML = mx.WeatherHelper.formatNumber(data["weekMinTemperature"]);
            mx.$(".week .summary .temperature .value span.max").innerHTML = mx.WeatherHelper.formatNumber(data["weekMaxTemperature"]);
            mx.$(".week .summary .wind .value span").innerHTML = mx.WeatherHelper.formatNumber(data["weekMaxWindSpeed"]);
            mx.$(".week .summary .rain .value span").innerHTML = mx.WeatherHelper.formatNumber(data["weekSumRain"]);
            mx.$(".week .summary .sun .value span").innerHTML = mx.WeatherHelper.formatDuration(data["weekSumSunshine"]);

            let html_rows = [];
            data["weekList"].forEach(function(row)
            {
                let start = new Date();
                start.setTime(Date.parse(row["start"]));

                let is_active = ( now.getDate() == start.getDate() && now.getMonth() == start.getMonth() );

                let time = '<div>' + mx.WeatherHelper.formatWeekdayName(start) + '</div><div>' + mx.WeatherHelper.formatWeekdayDate(start) + '</div>';
                let clickDate = start.getFullYear() + '-' + mx.WeatherHelper.formatLeadingZero(start.getMonth() + 1) + '-' + mx.WeatherHelper.formatLeadingZero(start.getDate());
                let id = "week_" + clickDate;
                let html_row = buildRow(
                    id,
                    time,
                    row["svg"],
                    row["maxAirTemperatureInCelsius"],
                    row["minAirTemperatureInCelsius"],
                    row["sunshineDurationInMinutes"],
                    row["precipitationProbabilityInPercent"],
                    row["precipitationAmountInMillimeter"],
                    row["windSpeedInKilometerPerHour"],
                    row["windDirectionInDegree"],
                    clickDate
                );
                html_rows.push(html_row);
            });

            mx.$(".week .hours").innerHTML = html_rows.length > 0 ? html_rows.join("") : mx.I18N.get("No forecasts available");;

            function clickHandler()
            {
                var day = this.getAttribute("mv-date");
                refreshWeek(day);
            }

            var elements = document.querySelectorAll('div[mv-date]');
            for( var i = 0; i < elements.length; i++)
            {
                var element = elements[i];
                element.addEventListener("click",clickHandler);
            }
        }

        mx.$$(".week .hours .active").forEach(function(element)
        {
            element.classList.remove("active");
        });

        if( mx.WeatherCore.active_day ) mx.$("#week_" + mx.WeatherCore.active_day.getFullYear() + '-' + mx.WeatherHelper.formatLeadingZero(mx.WeatherCore.active_day.getMonth() + 1) + '-' + mx.WeatherHelper.formatLeadingZero(mx.WeatherCore.active_day.getDate()) ).classList.add("active");

        if( mx.$(".week").classList.contains("open") ) document.getElementById("weekButton").click();
    }

    ret.init = function()
    {
        mx.I18N.process(document);

        initButtons();

        mx.Page.refreshUI();
    }
    return ret;
})( mx.WeatherCore || {} );

mx.OnDocReady.push( mx.WeatherCore.init );

var processData = mx.OnDocReadyWrapper( mx.WeatherCore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    mx.WeatherCore.socket = mx.ServiceSocket.init('weather_service', 'details', function(){
        return mx.WeatherCore.active_day == null ? null : mx.WeatherCore.active_day.getFullYear() + '-' + mx.WeatherHelper.formatLeadingZero(mx.WeatherCore.active_day.getMonth() + 1) + '-' + mx.WeatherHelper.formatLeadingZero(mx.WeatherCore.active_day.getDate())
    });
    mx.WeatherCore.socket.on("data", (data) => processData( data ) );
});

</script>
</head>
<body>
<script>
var theme = null;
try{
    var current = window;
    while( current )
    {
        current.location.host; // trigger exception on different (openhab) domain
        /*if( current.location.pathname.includes("habpanel") )
        {
            break;
        }*/
        current = current != current.parent ? current.parent : null;
    }
}
catch(e){
    // habpanel with different (openhab) domain
    theme = 'dark';
    document.querySelector("body").classList.add("black");
}
</script>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Weather"), theme); } );</script>
<div class="current">
    <div class="headline">
        <div class="title" data-i18n="Current"></div>
        <div id="rainButton" class="form button">Radar</div>
    </div>
    <div class="content">
        <div class="summary">
            <div class="column">
                <div class="cell temperature"><div class="icon"><?php echo getSVG('temperature', 'temperature_grayscaled'); ?></div><div class="name" data-i18n="Temperature"></div><div class="value"></div></div>
                <div class="cell perceived"><div class="icon"><?php echo getSVG('temperature', 'temperature_grayscaled'); ?></div><div class="name" data-i18n="Perceived"></div><div class="value"></div></div>
            </div>
            <div class="column">
                <div class="cell wind"><div class="icon"><?php echo getSVG('wind', 'wind_grayscaled'); ?></div><div class="name" data-i18n="Wind"></div><div class="value"></div></div>
                <div class="cell rain"><div class="icon"><?php echo getSVG('rain', 'rain_grayscaled'); ?></div><div class="name" data-i18n="Rain"></div><div class="value"></div></div>
            </div>
            <div class="column cloud"></div>
            <div class="column wrap"></div>
            <div class="column">
                <div class="cell sunrise"><div class="icon"><?php echo getSVG('sun', 'sun_grayscaled'); ?></div><div class="name" data-i18n="Sunrise"></div><div class="value"></div></div>
                <div class="cell sunset"><div class="icon"><?php echo getSVG('sun', 'sun_grayscaled'); ?></div><div class="name" data-i18n="Sunset"></div><div class="value"></div></div>
            </div>
            <div class="column">
                <div class="cell uv"><div class="icon"><?php echo getSVG('sun', 'sun_grayscaled'); ?></div><div class="name" data-i18n="UV Index"></div><div class="value"></div></div>
                <div class="cell"></div>
            </div>
            <div class="column dummy"></div>
        </div>
    </div>
</div>

<div class="forecast">
    <div class="today">
        <div class="headline">
            <div class="title" data-i18n="Day"></div>
            <div id="weekButton" data-i18n="Week" class="form button"></div>
        </div>
        <div class="summary">
            <div class="cell temperature"><div class="icon"><?php echo getSVG('temperature', 'temperature_grayscaled'); ?></div><div class="value"><span class="max"></span><span class="min"></span> °C</div></div>
            <div class="cell wind"><div class="icon"><?php echo getSVG('wind', 'wind_grayscaled'); ?></div><div class="value"><span></span> km/h</div></div>
            <div class="cell rain"><div class="icon"><?php echo getSVG('rain', 'rain_grayscaled'); ?></div><div class="value"><span></span> mm</div></div>
            <div class="cell sun"><div class="icon"><?php echo getSVG('sun', 'sun_grayscaled'); ?></div><div class="value"><span></span></div></div>
        </div>
        <div class="hours">
            <div class="hour" data-i18n="No forecasts available"></div>
        </div>
    </div>
    <div class="week">
        <div class="headline">
            <div class="title" data-i18n="Week"></div>
        </div>
        <div class="summary">
            <div class="cell temperature"><div class="icon"><?php echo getSVG('temperature', 'temperature_grayscaled'); ?></div><div class="value temperature"><span class="max"></span><span class="min"></span> °C</div></div>
            <div class="cell wind"><div class="icon"><?php echo getSVG('wind', 'wind_grayscaled'); ?></div><div class="value"><span></span> km/h</div></div>
            <div class="cell rain"><div class="icon"><?php echo getSVG('rain', 'rain_grayscaled'); ?></div><div class="value"><span></span> mm</div></div>
            <div class="cell sun"><div class="icon"><?php echo getSVG('sun', 'sun_grayscaled'); ?></div><div class="value"><span></span></div></div>
        </div>
        <div class="hours">
            <div class="hour" data-i18n="No forecasts available"></div>
        </div>
    </div>
</div>

<div id="rainFrame"><iframe src=""></iframe></div>
<script>
</script>
</body>
</html>
