<?php
include dirname(__FILE__) . "/config.php";

$datetime = new DateTime();
$datetime->setTime($datetime->format("H"), 0, 0, 0);

$data = apcu_fetch( "currentWeatherIcon" );

if( empty($data) || $data[0] < $datetime->format("U") )
{
    include dirname(__FILE__) . "/lib/MySQL.php";
    include dirname(__FILE__) . "/lib/Weather.php";

    $mysql_db = new MySQL( DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME );

    $db_data = $mysql_db->getWeatherData( 0 );
    $blockData = Weather::initBlockData( $db_data['datetime'] );
    Weather::applyBlockData($blockData,$db_data);

    $data = array( $datetime->format("U"), Weather::convertOctaToSVG($blockData['from'], $blockData, 1) );
    apcu_store( "currentWeatherIcon", $data );
}

echo $data[1];
