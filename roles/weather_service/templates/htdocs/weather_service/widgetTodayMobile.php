<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

function getSVG( $icon, $id)
{
    return str_replace("\n", "", file_get_contents('icons/svg/' . $id . '.svg') );
}

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $_SERVER["REQUEST_SCHEME"] . "://" . $_SERVER["SERVER_NAME"]  . "/weather_service/api/widgetData/");
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "mode=mobile");

curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$result = curl_exec($ch);
curl_close($ch);

//print_r($values);

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/weather_service/"]); ?>
<script>
var json_data = <?php echo json_encode($result); ?>;
var data = JSON.parse(json_data);

var block_title = {
	'21': 'Night',
	'16': 'Evening',
	'11': 'Lunch',
	'6': 'Morning',
	'1': 'Night'
};

mx.WeatherCore = (function( ret ) {

    ret.init = function()
    {

        console.log(data);

        mx.I18N.process(document);

        mx.$(".summary .cloud").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentCloudsAsSVG"]);

        mx.$(".summary .temperature .value").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentAirTemperatureInCelsius"]) + ' °';
        mx.$(".summary .perceived .value").innerHTML = mx.I18N.get("Perceived") + " " + mx.WeatherHelper.formatNumber(data["current"]["currentPerceivedTemperatureInCelsius"]) + ' °';

        mx.$(".summary .rain_probability .value").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentRainProbabilityInPercent"]) + ' %';
        mx.$(".summary .rain_ammount .value").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentRainLastHourInMillimeter"]) + ' mm';

        mx.$(".summary .sunshine .value").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentSunshineDurationInMinutes"]) + ' min';
        mx.$(".summary .wind .value").innerHTML = mx.WeatherHelper.formatNumber(data["current"]["currentWindSpeedInKilometerPerHour"]) + ' km/h';

        var blockNode = mx.$(".details .block");
        data["forecast"]["dayList"].forEach(function(data)
        {
            var start = new Date(data["start"]);
            var _blockNode = blockNode.cloneNode(true);
            mx._$(".name", _blockNode).innerHTML = mx.WeatherHelper.formatHour(start);// + " - " + mx.I18N.get(block_title[start.getHours()]);
            mx._$(".cloud", _blockNode).innerHTML = data["svg"];
            mx._$(".temperature .real", _blockNode).innerHTML = Number((data["airTemperatureInCelsius"]).toFixed(0)) + "°";
            mx._$(".temperature .perceived", _blockNode).innerHTML = Number((data["minAirTemperatureInCelsius"]).toFixed(0)) + "°";

            blockNode.parentNode.appendChild(_blockNode);
            //console.log(_blockNode.innerHTML);
        });
        blockNode.parentNode.removeChild(blockNode);
    }

    return ret;
})( mx.WeatherCore || {} );

mx.OnDocReady.push( mx.WeatherCore.init );

</script>
<style>
.cloud svg {
    --svg-weather-clouds-stroke: gray;
    --svg-weather-clouds-stroke-width: 1px;
    --svg-weather-clouds-fill: white;
    --svg-weather-sun-stroke: #ffd427;
    --svg-weather-sun-stroke-width: 1px;
    --svg-weather-sun-fill: #ffd427;
    --svg-weather-moon-stroke: white;
    --svg-weather-moon-stroke-width: 1px;
    --svg-weather-moon-fill: white;
    --svg-weather-stars-stroke: gray;
    --svg-weather-stars-stroke-width: 0.5px;
    --svg-weather-stars-fill: white;
    --svg-weather-thunder-stroke: rgba(255, 165, 0, 1.0);
    --svg-weather-thunder-stroke-width: 1px;
    --svg-weather-thunder-fill: rgba(255, 165, 0, 0.2);
    --svg-weather-raindrop-stroke: #0055ff;
    --svg-weather-raindrop-stroke-width: 4px;
    --svg-weather-raindrop-fill: #0055ff;
    --svg-weather-snowflake-stroke: #0055ff;
    --svg-weather-snowflake-stroke-width: 1px;
    --svg-weather-snowflake-fill: #0055ff;

    width: 58px;
	height: 58px;
}
body {
    margin: 0;
}
.content {
    padding: 0 10px
}
.summary, .details {
    display: flex;
    flex-grow: 1;
    justify-content: space-between;
    color: white;
    font-size: 12px;
}
.summary .temperature {
    font-size: 16px;
    font-weight: bold;
}
.summary .block {
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.details {
    margin-top: -5px;
}
.block > div {
    display: flex;
}
.block >.value {
    color: white;
}
.block .icon {
    margin-right: 3px;
}
.block .icon svg {
    width: 16px;
    height: 16px;
    stroke: gray;
    fill: #ffffff80;
}
.details svg {
    width: 40px;
    height: 40px;
}
.details .temperature .real {
    margin-right: 3px;
    font-weight: bold;
}
</style>
</head>
<body style="background-color:transparent">
<div class="content">
    <div class="summary">
        <div class="block cloud"></div>
        <div class="block">
            <div class="temperature"><div class="value"></div></div>
            <div class="perceived"><div class="value"></div></div>
        </div>
        <div class="block">
            <div class="rain_probability"><div class="icon"><?php echo getSVG('wind', 'rain_grayscaled'); ?></div><div class="value"></div></div>
            <div class="sunshine"><div class="icon"><?php echo getSVG('rain', 'sun_grayscaled'); ?></div><div class="value"></div></div>
        </div>
        <div class="block">
            <div class="rain_ammount"><div class="icon"><?php echo getSVG('raindrop', 'raindrop_grayscaled'); ?></div><div class="value"></div></div>
            <div class="wind"><div class="icon"><?php echo getSVG('wind', 'wind_grayscaled'); ?></div><div class="value"></div></div>
        </div>
    </div>
    <div class="details">
        <div class="block">
            <div class="name"></div>
            <div class="cloud"></div>
            <div class="temperature"><div class="real"></div><div class="perceived"></div></div>
        </div>
    </div>
</div>
</body>
</html>

