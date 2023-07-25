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
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link href="<?php echo Ressources::getCSSPath('/weather_service/'); ?>" rel="stylesheet">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/weather_service/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/weather_service/'); ?>"></script>
<script>
var theme = "";
if( document.cookie.indexOf("theme=") != -1 )
{
    var cookies = document.cookie.split(";");
    for(var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].split("=");
        if( cookie[0].trim() == "theme" )
        {
            theme = cookie[1].trim();
            break;
        }
    }
}
else
{
    var isPhone = ( navigator.userAgent.indexOf("Android") != -1 && navigator.userAgent.indexOf("Mobile") != -1 );
    theme = isPhone ? 'black' : 'light';
}

var basicui = false;
try{
    var current = window;
    while( current )
    {
        if( current.location.pathname.includes("habpanel") )
        {
            theme = 'black';
            break;
        }
        current = current != current.parent ? current.parent : null;
    }
    if( parent.location.pathname.indexOf("basicui")!==-1 )
    {
        basicui = true;
    }
}
catch(e){}

document.querySelector("html").classList.add(theme);
document.querySelector("html").classList.add(theme == "light" ? "lightTheme" : "darkTheme" );

if( basicui )
{
    document.body.classList.add("basicui");
}

mx.WeatherCore = (function( ret ) {
    //var serviceApiUrl = mx.Host.getBase() + '../api/';
    var serviceApiUrl = mx.Host.getBase() + '../../weather_service/api/';

    var active_day = null;
    var refreshTimer = 0;
    var lastModified = [];
    var currentValues = []

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

    function handleState(data)
    {
        //console.log(data);

        let changedValues = data["changed_data"];

        currentValues = Object.assign(currentValues, changedValues);

        if( "dayActive" in changedValues )
        {
            active_day = new Date();
            active_day.setTime(Date.parse(currentValues["dayActive"]));
            mx.$(".today .title").innerHTML = mx.WeatherHelper.formatDay(active_day);
        }

        let now = new Date();

        if( "airTemperatureInCelsius" in changedValues) mx.$(".current .summary .temperature .value").innerHTML = mx.WeatherHelper.formatNumber(currentValues["airTemperatureInCelsius"]) + ' °C';
        if( "perceivedTemperatureInCelsius" in changedValues) mx.$(".current .summary .perceived .value").innerHTML = mx.WeatherHelper.formatNumber(currentValues["perceivedTemperatureInCelsius"]) + ' °C';

        if( "windSpeedInKilometerPerHour" in changedValues || "windGustInKilometerPerHour" in changedValues )
        {
            let windSpeed = mx.WeatherHelper.formatNumber(currentValues["windSpeedInKilometerPerHour"]);
            let windGust = mx.WeatherHelper.formatNumber(currentValues["windGustInKilometerPerHour"]);
            let wind = windSpeed;
            if( windSpeed != windGust && currentValues["windGustInKilometerPerHour"] > 0 )
            {
                wind += ' (' + windGust + ')';
            }
            mx.$(".current .summary .wind .value").innerHTML = wind + ' km/h';
        }

        if( "rainCurrentInMillimeter" in changedValues || "rainDailyInMillimeter" in changedValues )
        {
            let rainValue = mx.WeatherHelper.formatNumber(currentValues["rainCurrentInMillimeter"]);
            let rainDaily = mx.WeatherHelper.formatNumber(currentValues["rainDailyInMillimeter"]);
            let rain = rainValue
            if( rainValue != rainDaily && currentValues["rainDailyInMillimeter"] > 0 )
            {
                rain += ' (' + rainDaily + ')';
            }
            mx.$(".current .summary .rain .value").innerHTML = rain + ' mm';
        }

        if( "currentCloudsAsSVG" in changedValues) mx.$(".current .cloud").innerHTML = mx.WeatherHelper.formatNumber(currentValues["currentCloudsAsSVG"]);

        if( "dayList" in changedValues)
        {
            mx.$(".today .summary .temperature .value span.min").innerHTML = mx.WeatherHelper.formatNumber(currentValues["dayMinTemperature"]);
            mx.$(".today .summary .temperature .value span.max").innerHTML = mx.WeatherHelper.formatNumber(currentValues["dayMaxTemperature"]);
            mx.$(".today .summary .wind .value span").innerHTML = mx.WeatherHelper.formatNumber(currentValues["dayMaxWindSpeed"]);
            mx.$(".today .summary .rain .value span").innerHTML = mx.WeatherHelper.formatNumber(currentValues["daySumRain"]);
            mx.$(".today .summary .sun .value span").innerHTML = mx.WeatherHelper.formatDuration(currentValues["daySumSunshine"]);

            let html_rows = [];
            let active_id = null;
            currentValues["dayList"].forEach(function(row)
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

            mx.$(".today .hours").innerHTML = html_rows.join("");
            if( active_id ) mx.$("#" + active_id ).classList.add("active");
        }

        if( "weekList" in changedValues)
        {
            mx.$(".week .summary .temperature .value span.min").innerHTML = mx.WeatherHelper.formatNumber(currentValues["weekMinTemperature"]);
            mx.$(".week .summary .temperature .value span.max").innerHTML = mx.WeatherHelper.formatNumber(currentValues["weekMaxTemperature"]);
            mx.$(".week .summary .wind .value span").innerHTML = mx.WeatherHelper.formatNumber(currentValues["weekMaxWindSpeed"]);
            mx.$(".week .summary .rain .value span").innerHTML = mx.WeatherHelper.formatNumber(currentValues["weekSumRain"]);
            mx.$(".week .summary .sun .value span").innerHTML = mx.WeatherHelper.formatDuration(currentValues["weekSumSunshine"]);

            let html_rows = [];
            currentValues["weekList"].forEach(function(row)
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

            mx.$(".week .hours").innerHTML = html_rows.join("");

            function clickHandler()
            {
                var day = this.getAttribute("mv-date");
                delete lastModified["provider"];
                refreshState(lastModified, day);
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
        mx.$("#week_" + active_day.getFullYear() + '-' + mx.WeatherHelper.formatLeadingZero(active_day.getMonth() + 1) + '-' + mx.WeatherHelper.formatLeadingZero(active_day.getDate()) ).classList.add("active");

        if( mx.$(".week").classList.contains("open") ) document.getElementById("weekButton").click();
    }

    function refreshState(last_data_modified, day)
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", serviceApiUrl + "data/" );
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

        //application/x-www-form-urlencoded

        window.clearTimeout(refreshTimer);

        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;

            if( this.status == 200 )
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    mx.Error.confirmSuccess();

                    handleState(response);

                    lastModified = response["last_data_modified"]
                    refreshTimer = window.setTimeout(function(){ refreshState(response["last_data_modified"], day) }, 60000);
                }
                else
                {
                    mx.Error.handleServerError( mx.I18N.get( "Service is currently not available")  );
                }
            }
            else
            {
                let timeout = 15000;
                if( this.status == 0 || this.status == 503 )
                {
                    mx.Error.handleError( mx.I18N.get( "Service is currently not available")  );
                }
                else
                {
                    if( this.status != 401 ) mx.Error.handleRequestError(this.status, this.statusText, this.response);
                }

                mx.Page.handleRequestError(this.status, serviceApiUrl, function(){ refreshState(last_data_modified, day) }, timeout);
            }
        };

        let params = { "type": "week", "fields": "dayList,weekList,airTemperatureInCelsius,perceivedTemperatureInCelsius,windSpeedInKilometerPerHour,windGustInKilometerPerHour,rainCurrentInMillimeter,rainDailyInMillimeter,currentCloudsAsSVG", "last_data_modified": last_data_modified }
        if( day ) params["day"] = day;
        xhr.send(mx.Core.encodeDict( params ));
    }

    function initButtons()
    {
        var weekButton = document.getElementById("weekButton");
        weekButton.addEventListener("click",function(){
            var weekList = document.querySelector(".forecast .week");
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

    ret.init = function()
    {
        mx.I18N.process(document);

        refreshState();
        initButtons();
    }
    return ret;
})( mx.WeatherCore || {} );

mx.OnDocReady.push( mx.WeatherCore.init );

</script>
</head>
<body>
<div class="current">
    <div class="headline">
        <div class="title" data-i18n="Current"></div>
        <div id="rainButton">Radar</div>
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
        </div>
        <div class="cloud"></div>
    </div>
</div>

<div class="forecast">
    <div class="today">
        <div class="headline">
            <div class="title" data-i18n="Day"></div>
            <div id="weekButton" data-i18n="Week"></div>
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
