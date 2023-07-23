<?php
include dirname(__FILE__) . "/lib/MySQL.php";
include dirname(__FILE__) . "/lib/Weather.php";
include dirname(__FILE__) . "/config.php";

$mysql_db = new MySQL( DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME );

$activeDay = empty($_GET["date"]) ? new DateTime() : DateTime::createFromFormat('Y-m-d',$_GET["date"]);

$isToday = empty($_GET["date"]) || $activeDay->format("Y-m-d") == (new DateTime())->format("Y-m-d");

/**** SUMMERY ****/
$from = clone $activeDay;
$from->setTime(0,0,0);
$to = clone $from;
$to->setTime(23,59,59);
$dayList = $mysql_db->getWeatherDataList($from, $to);

if( $dayList )
    {
    list( $minTemperature, $maxTemperature, $maxWindSpeed, $sumSunshine, $sumRain ) = Weather::calculateSummary( $dayList );

    //echo Weather::formatDay($activeDay);

    /**** DAYLIST ****/
    $from = clone $activeDay;
    if( $isToday )
    {
        $from->setTime(0,0,0);
    }
    else{
        $from->setTime(0,0,0);
        //$from->sub(new DateInterval('PT24H'));
    }
    $to = clone $activeDay;
    $to->setTime(24,00,00);

    $dayList = $mysql_db->getWeatherDataList($from, $to);

    $todayValues = array();
    $current_value = Weather::initBlockData( reset( $dayList )['datetime']);
    $index = 0;

    foreach( $dayList as $hourlyData  ){
        //echo ( $index ) . "<br>";
        
        if( $index > 0 && $index % 3 == 0 )
        {
            $current_value['to'] = $hourlyData['datetime'];
            $todayValues[] = $current_value;
            $current_value = Weather::initBlockData($hourlyData['datetime']);
            //echo $hourlyData['datetime']."<br>";
        }
        
        Weather::applyBlockData($current_value,$hourlyData);

        $index++;
    }
    $current_value['to'] = ( clone $hourlyData['datetime'] )->add(new DateInterval('PT1H'));;
    $todayValues[] = $current_value;

    //echo print_r($dayList,true);
    //echo print_r($todayValues,true);

    /**** WEEKLIST ****/
    $weekFrom = new DateTime();
    $weekFrom->setTime(0,0,0);

    $weekList = $mysql_db->getWeatherDataWeekList($weekFrom);
    //echo print_r($weekList,true);

    list( $minTemperatureWeekly, $maxTemperatureWeekly, $maxWindSpeedWeekly, $sumSunshineWeekly, $sumRainWeekly ) = Weather::calculateSummary( $weekList );

    $weekValues = array();
    $weekList[0]['datetime']->setTime(10,0,0);
    $current_value = Weather::initBlockData( $weekList[0]['datetime'] );
    $index = 1;
    foreach( $weekList as $hourlyData )
    {
        $hourlyData['datetime']->setTime(10,0,0);

        //echo $hourlyData['datetime']." ".$current_value['from'] . "\n\n";
        if( $hourlyData['datetime'] != $current_value['from'] )
        {
            $current_value['to'] = $current_value['from'];
            $weekValues[] = $current_value;
            $current_value = Weather::initBlockData($hourlyData['datetime']);
            
            //echo $hourlyData['datetime']."<br>";
        }
        
        Weather::applyBlockData($current_value,$hourlyData);

        $index++;
    }
}
else
{
    $hourlyData = [];
}
//$current_value['to'] = ( clone $hourlyData['datetime'] )->add(new DateInterval('PT1H'));;
//$weekValues[] = $current_value;

//echo print_r($weekValues,true);

?>
<div class="weatherForecast weatherDetailForecast">
	<div class="today">
		<div class="title">
            <?php /*echo time();*/ echo Weather::formatDay($activeDay); ?>
		</div>
		<div class="summary">
			<div class="cell"><div class="icon temperature"><?php echo Weather::getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value temperature\"><span class=\"max\">" . $maxTemperature . "</span><span class=\"min\">" . $minTemperature ; ?></span> °C</div></div>
			<div class="cell"><div class="icon wind"><?php echo Weather::getSVG('wind', 'wind_grayscaled') . "</div><div class=\"value\">" . $maxWindSpeed; ?> km/h</div></div>
            <div class="cell"><div class="icon rain"><?php echo Weather::getSVG('rain', 'rain_grayscaled') . "</div><div class=\"value\">" . $sumRain; ?> mm</div></div>
            <div class="cell"><div class="icon sun"><?php echo Weather::getSVG('sun', 'sun_grayscaled') . "</div><div class=\"value\">" . Weather::formatDuration( $sumSunshine ); ?></div></div>
		</div>
        <div class="hours">
<?php
    if( !$hourlyData )
    {
?>
            <div class="hour">Keine Vorhersagedaten vorhanden</div>
<?php 
    }
    else
    {
        $i=0;
        $now = new Datetime();
        foreach( $todayValues as $hourlyData ){  
            #$hourlyData['effectiveCloudCoverInOcta'] = 3;//$i;
            #$hourlyData['precipitationProbabilityInPercent'] = 40;
            #$hourlyData['precipitationAmountInMillimeter'] = $i * 0.6;
            #$hourlyData['thunderstormProbabilityInPercent'] = 40;
            $i++;

            $isActive = $now >= $hourlyData["from"] && $now < $hourlyData["to"];
?>
            <div class="hour<?php echo ( $isActive ? " active" : "" ); ?>">
                <div class="time"><div class="from"><?php echo Weather::formatHour($hourlyData['from']) /*. ' -</div><div class="to">' . Weather::formatHour($hourlyData['to'])*/ ; ?></div></div>
                <div class="cloud"><?php echo Weather::convertOctaToSVG($hourlyData['from'],$hourlyData,3);?>
                </div>
                <div class="temperature">
                    <div>
                        <div class="main"><span class="max"><?php echo $hourlyData['maxAirTemperatureInCelsius'] . '</span><span class="min">' . $hourlyData['minAirTemperatureInCelsius'] ; ?></span></div><div class="sub">°C</div>
                    </div>
                </div>
                <div class="info">
                    <div class="sunshineDuration"><div class="sun"><?php echo Weather::getSVG('sun', 'sun_grayscaled') . "</div><div>" . Weather::formatDuration( $hourlyData['sunshineDurationInMinutesSum'] ); ?></div></div>
                    <div class="precipitationProbability"><div><?php echo Weather::getSVG('rain','rain_grayscaled') . "</div><div>" . $hourlyData['precipitationProbabilityInPercent']; ?> %</div></div>
                    <div class="precipitationAmount"><div></div><div><?php echo $hourlyData['precipitationAmountInMillimeterSum']; ?> mm</div></div>
                </div>
                <div class="wind">
                    <div>
                        <div><?php echo $hourlyData['windSpeedInKilometerPerHour']; ?> km/h</div>
                        <div class="compass">
                            <div class="circle"><?php echo Weather::getSVG('compass_circle', 'compass_circle_grayscaled'); ?></div>
                            <div class="needle" style="transform: rotate(<?php echo ( $hourlyData['windDirectionInDegree'] - 180 ); ?>deg)"><?php echo Weather::getSVG('compass_needle', 'compass_needle_grayscaled'); ?></div>
                        </div>
                    </div>
                </div>
            </div>
<?php   }
    }?>
        </div>
    </div>
	<div class="week">
		<div class="title">
            Woche
		</div>
		<div class="summary">
			<div class="cell"><div class="icon temperature"><?php echo Weather::getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value temperature\"><span class=\"max\">" . $maxTemperatureWeekly . "</span><span class=\"min\">" . $minTemperatureWeekly ; ?></span> °C</div></div>
			<div class="cell"><div class="icon wind"><?php echo Weather::getSVG('wind', 'wind_grayscaled') . "</div><div class=\"value\">" . $maxWindSpeedWeekly; ?> km/h</div></div>
            <div class="cell"><div class="icon rain"><?php echo Weather::getSVG('rain', 'rain_grayscaled') . "</div><div class=\"value\">" . $sumRainWeekly; ?> mm</div></div>
            <div class="cell"><div class="icon sun"><?php echo Weather::getSVG('sun', 'sun_grayscaled') . "</div><div class=\"value\">" . Weather::formatDuration( $sumSunshineWeekly ); ?></div></div>
		</div>
		<div class="hours">
<?php 
    if( !$hourlyData )
    {
?>
            <div class="hour">Keine Vorhersagedaten vorhanden</div>
<?php 
    }
    else
    {
        foreach( $weekValues as $hourlyData )
        { 
            $clickUrl = $_SERVER['SCRIPT_URL'] . '?date=' . $hourlyData['from']->format("Y-m-d");
            //$hourlyData['effectiveCloudCoverInOcta'] = array_search($hourlyData,$weekValues) * 1.2;
?>
            <div class="hour mvClickable<?php if( $activeDay->format("Y-m-d") == $hourlyData['from']->format("Y-m-d") ) echo " active"; ?>" mv-url="<?php echo $clickUrl;?>">
                <div class="time"><div><?php echo Weather::formatWeekdayName($hourlyData['from']) . '</div><div>' . Weather::formatWeekdayDate($hourlyData['to']) ; ?></div></div>
                <div class="cloud"><?php echo Weather::convertOctaToSVG($hourlyData['to'],$hourlyData,24);?>
                </div>
                <div class="temperature">
                    <div>
                        <div class="main"><span class="max"><?php echo $hourlyData['maxAirTemperatureInCelsius'] . '</span><span class="min">' . $hourlyData['minAirTemperatureInCelsius'] ; ?></span></div><div class="sub">°C</div>
                    </div>
                </div>
                <div class="info">
                    <div class="sunshineDuration"><div class="sun"><?php echo Weather::getSVG('sun', 'sun_grayscaled') . "</div><div>" . Weather::formatDuration( $hourlyData['sunshineDurationInMinutesSum'] ); ?></div></div>
                    <div class="precipitationProbability"><?php echo Weather::getSVG('rain', 'rain_grayscaled') . " " . $hourlyData['precipitationProbabilityInPercent']; ?> %</div>
                    <div class="precipitationAmount"><div></div><div><?php echo $hourlyData['precipitationAmountInMillimeterSum']; ?> mm</div></div>
                </div>
                <div class="wind">
                    <div>
                        <div><?php echo $hourlyData['windSpeedInKilometerPerHour']; ?> km/h</div>
                        <div class="compass">
                            <div class="circle"><?php echo Weather::getSVG('compass_circle', 'compass_circle_grayscaled'); ?></div>
                            <div class="needle" style="transform: rotate(<?php echo ( $hourlyData['windDirectionInDegree'] - 180 ); ?>deg)"><?php echo Weather::getSVG('compass_needle', 'compass_needle_grayscaled'); ?></div>
                        </div>
                    </div>
                </div>
                <div class="status"></div>
            </div>
<?php   }
    }?>
        </div>
	</div>
</div>
