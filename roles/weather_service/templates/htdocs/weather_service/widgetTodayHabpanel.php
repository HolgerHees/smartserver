<?php
$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $_SERVER["REQUEST_SCHEME"] . "://" . $_SERVER["SERVER_NAME"]  . "/weather_service/api/widgetData/");
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "mode=habpanel");

curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$result = curl_exec($ch);
curl_close($ch);

$values = json_decode($result);

/******* OVERVIEW ************/
$blockConfigs = array(
	'21' => array( 'title' => "Nachts", 'class' => 'night' ),
	'16' => array( 'title' => "Abends", 'class' => 'evening' ),
	'11' => array( 'title' => "Mittags", 'class' => 'lunch' ),
	'06' => array( 'title' => "Früh", 'class' => 'morning' ),
	'01' => array( 'title' => "Nachts", 'class' => 'night' ),
);

$blockHours = [];
foreach( $values->dayList as $blockData )
{
    $blockHours[$blockData->start] = DateTime::createFromFormat("Y-m-d\TH:i:s",$blockData->start)->format("H");
}

function getSVG( $icon, $id)
{
    return file_get_contents('icons/svg/' . $id . '.svg');
}

function formatDuration($duration)
{
    if( $duration < 180 ) return $duration . " min.";
    return round( $duration / 60 ) . " h";
}

function formatNumber($number, $precission = 1)
{
    return number_format($number, $precission);
}

//echo print_r($values,true);
?>
<div class="weatherForecast weatherTodayForecast">
	<?php /*echo time();*/ ?>
	<div class="headlines">
<?php foreach( $values->dayList as $blockData ){ ?>
        <div class="cell"><?php echo $blockConfigs[$blockHours[$blockData->start]]['title']; ?></div>
<?php } ?>
	</div>
	<div class="details">
<?php
    foreach( $values->dayList as $blockData ){
        $start = DateTime::createFromFormat("Y-m-d\TH:i:s",$blockData->start);
        $end = DateTime::createFromFormat("Y-m-d\TH:i:s",$blockData->end);
?>
		<div class="cell <?php echo $blockConfigs[$blockHours[$blockData->start]]['title']; ?>">
            <div class="time"><div class="from"><?php echo $start->format("H:i") . ' -</div><div class="to">' . $end->format("H:i"); ?></div></div>
            <div class="sun"><?php echo $blockData->svg; ?>
            </div>
            <div class="value temperature"><div class="main"><?php echo formatNumber($blockData->airTemperatureInCelsius); ?></div><div class="sub">&nbsp;°C</div></div>
            <div class="value precipitationProbability">
                <?php echo getSVG('rain', 'rain_grayscaled') . "<div class=\"main\">" . formatNumber($blockData->precipitationProbabilityInPercent, 0); ?></div><div class="sub">&nbsp;%</div>
            </div>
            <div class="value precipitationAmount">
                <div class="main"><?php echo formatNumber($blockData->precipitationAmountInMillimeter); ?></div><div class="sub">&nbsp;mm</div>
            </div>
		</div>
<?php } ?>
	</div>
	<div class="summary">
		<div class="cell"><div class="txt">Min.:</div><div class="icon temperature"><?php echo getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value\">" . formatNumber($values->dayMinTemperature); ?>&nbsp;°C</div></div>
		<div class="bullet">•</div>
		<div class="cell"><div class="txt">Max.:</div><div class="icon temperature"><?php echo getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value\">" . formatNumber($values->dayMaxTemperature); ?>&nbsp;°C</div></div>
		<div class="bullet">•</div>
		<div class="cell"><div class="txt">Max.:</div><div class="icon wind"><?php echo getSVG('wind', 'wind_grayscaled') . "</div><div class=\"value\">" . formatNumber($values->dayMaxWindSpeed); ?>&nbsp;km/h</div></div>
		<div class="bullet">•</div>
		<div class="cell"><div class="txt">Sum:</div><div class="icon rain"><?php echo getSVG('rain', 'rain_grayscaled') . "</div><div class=\"value\">" . formatNumber($values->daySumRain); ?>&nbsp;mm</div></div>
		<div class="bullet">•</div>
		<div class="cell"><div class="txt">Dauer:</div><div class="icon sun"><?php echo getSVG('sun', 'sun_grayscaled') . "</div><div class=\"value\">" . formatDuration( $values->daySumSunshine ); ?></div></div>
	</div>
</div>
