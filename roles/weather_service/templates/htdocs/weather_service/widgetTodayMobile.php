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

$data = json_decode($result, true);

$i18n = Ressources::getI18NContentAsObject([__DIR__]);

/*$block_title = array(
	'21' => 'Night',
	'16' => 'Evening',
	'11' => 'Lunch',
	'6' => 'Morning',
	'1' => 'Night'
};*/

function getI18N($string, $i18n)
{
    return array_key_exists($string, $i18n["index"] ) ?  $i18n["index"][$string] : $string;
}
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
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
        <div class="block cloud"><?php echo $data["current"]["currentCloudsAsSVG"]; ?></div>
        <div class="block">
            <div class="temperature"><div class="value"><?php echo round($data["current"]["currentAirTemperatureInCelsius"], 1); ?>°</div></div>
            <div class="perceived"><div class="value"><?php echo getI18N("Perceived", $i18n) . " " . round($data["current"]["currentPerceivedTemperatureInCelsius"], 1); ?>°</div></div>
        </div>
        <div class="block">
            <div class="rain_probability"><div class="icon"><?php echo getSVG('wind', 'rain_grayscaled'); ?></div><div class="value"><?php echo round($data["current"]["currentRainProbabilityInPercent"], 0); ?> %</div></div>
            <div class="sunshine"><div class="icon"><?php echo getSVG('rain', 'sun_grayscaled'); ?></div><div class="value"><?php echo round($data["current"]["currentRainLastHourInMillimeter"], 1); ?> min</div></div>
        </div>
        <div class="block">
            <div class="rain_ammount"><div class="icon"><?php echo getSVG('raindrop', 'raindrop_grayscaled'); ?></div><div class="value"><?php echo round($data["current"]["currentSunshineDurationInMinutes"], 0); ?> mm</div></div>
            <div class="wind"><div class="icon"><?php echo getSVG('wind', 'wind_grayscaled'); ?></div><div class="value"><?php echo round($data["current"]["currentWindSpeedInKilometerPerHour"], 1); ?> km/h</div></div>
        </div>
    </div>
    <div class="details">
<?php foreach( $data["forecast"]["dayList"] as $day ) {?>
        <div class="block">
            <div class="name"><?php echo date_create($day["start"])->format("H:i"); ?></div>
            <div class="cloud"><?php echo $day["svg"]; ?></div>
            <div class="temperature"><div class="real"><?php echo round($day["airTemperatureInCelsius"], 0); ?>°</div><div class="perceived"><?php echo round($day["minAirTemperatureInCelsius"], 0); ?>°</div></div>
        </div>
<?php } ?>
    </div>
</div>
</body>
</html>

