<?php

class Weather
{
    private static $sunConfig = array(
        // possible icons and typeIconOffsetLeft
        'day' => array( 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ),
        'night' => array( 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy'	),
    );
    
    public static function initBlockData($from)
    {
        return array(
            'from' => $from,
            'to' => '',
            'sunshineDurationInMinutesSum' => 0,
            'precipitationAmountInMillimeterSum' => 0,
            'sunshineDurationInMinutes' => 0,
            'effectiveCloudCoverInOcta' => 0,
            'precipitationType' => -100,
            'thunderstormProbabilityInPercent' => 0,
            'freezingRainProbabilityInPercent' => 0,
            'hailProbabilityInPercent' => 0,
            'snowfallProbabilityInPercent' => 0,
            'precipitationProbabilityInPercent' => 0,
            'precipitationAmountInMillimeter' => 0,
            'airTemperatureInCelsius' => -100,
            'windSpeedInKilometerPerHour' => 0,
            'windDirectionInDegree' => 0
        );
    }
    
    public static function applyBlockData( &$current_value, $hourlyData )
    {
        $current_value['sunshineDurationInMinutesSum'] += $hourlyData['sunshineDurationInMinutes'];
        $current_value['precipitationAmountInMillimeterSum'] += $hourlyData['precipitationAmountInMillimeter'];

        if( !isset($current_value['minAirTemperatureInCelsius']) || $current_value['minAirTemperatureInCelsius'] > $hourlyData['airTemperatureInCelsius'] )
        {
            $current_value['minAirTemperatureInCelsius'] = $hourlyData['airTemperatureInCelsius'];
        }
        
        if( !isset($current_value['maxAirTemperatureInCelsius']) || $current_value['maxAirTemperatureInCelsius'] < $hourlyData['airTemperatureInCelsius'] )
        {
            $current_value['maxAirTemperatureInCelsius'] = $hourlyData['airTemperatureInCelsius'];
        }

        if( $current_value['sunshineDurationInMinutes'] < $hourlyData['sunshineDurationInMinutes'] )
        {
            $current_value['sunshineDurationInMinutes'] = $hourlyData['sunshineDurationInMinutes'];
        }
        if( $current_value['effectiveCloudCoverInOcta'] < $hourlyData['effectiveCloudCoverInOcta'] )
        {
            $current_value['effectiveCloudCoverInOcta'] = $hourlyData['effectiveCloudCoverInOcta'];
        }
        if( $current_value['precipitationType'] < $hourlyData['precipitationType'] ) 
        {
            $current_value['precipitationType'] = $hourlyData['precipitationType'];
        }
        if( $current_value['thunderstormProbabilityInPercent'] < $hourlyData['thunderstormProbabilityInPercent'] )
        {
            $current_value['thunderstormProbabilityInPercent'] = $hourlyData['thunderstormProbabilityInPercent'];
        }
        if( $current_value['freezingRainProbabilityInPercent'] < $hourlyData['freezingRainProbabilityInPercent'] )
        {
            $current_value['freezingRainProbabilityInPercent'] = $hourlyData['freezingRainProbabilityInPercent'];
        }
        if( $current_value['hailProbabilityInPercent'] < $hourlyData['hailProbabilityInPercent'] )
        {
            $current_value['hailProbabilityInPercent'] = $hourlyData['hailProbabilityInPercent'];
        }
        if( $current_value['snowfallProbabilityInPercent'] < $hourlyData['snowfallProbabilityInPercent'] )
        {
            $current_value['snowfallProbabilityInPercent'] = $hourlyData['snowfallProbabilityInPercent'];
        }
        if( $current_value['precipitationProbabilityInPercent'] < $hourlyData['precipitationProbabilityInPercent'] && $current_value['precipitationAmountInMillimeter'] > 0 )
        {
            $current_value['precipitationProbabilityInPercent'] = $hourlyData['precipitationProbabilityInPercent'];
        }
        if( $current_value['precipitationAmountInMillimeter'] < $hourlyData['precipitationAmountInMillimeter'] )
        {
            $current_value['precipitationAmountInMillimeter'] = $hourlyData['precipitationAmountInMillimeter'];
        }
        if( $current_value['airTemperatureInCelsius'] < $hourlyData['airTemperatureInCelsius'] )
        {
            $current_value['airTemperatureInCelsius'] = $hourlyData['airTemperatureInCelsius'];
        }
        if( $current_value['windSpeedInKilometerPerHour'] < $hourlyData['windSpeedInKilometerPerHour'] ) 
        {
            $current_value['windSpeedInKilometerPerHour'] = $hourlyData['windSpeedInKilometerPerHour'];
            $current_value['windDirectionInDegree'] = $hourlyData['windDirectionInDegree'];
        }
    }

    public static function calculateSummary( $dataList )
    {
		$minTemperature = $dataList[0]['airTemperatureInCelsius'];
		$maxTemperature = $dataList[0]['airTemperatureInCelsius'];
		$maxWindSpeed = $dataList[0]['windSpeedInKilometerPerHour'];
		$sumSunshine = 0;
		$sumRain = 0;

		foreach( $dataList as $entry  )
		{
			if( $minTemperature > $entry['airTemperatureInCelsius'] ) $minTemperature = $entry['airTemperatureInCelsius'];
			if( $maxTemperature < $entry['airTemperatureInCelsius'] ) $maxTemperature = $entry['airTemperatureInCelsius'];
			if( $maxWindSpeed < $entry['maxWindSpeedInKilometerPerHour'] ) $maxWindSpeed = $entry['maxWindSpeedInKilometerPerHour'];
			
			$sumSunshine += $entry['sunshineDurationInMinutes'];
			$sumRain += $entry['precipitationAmountInMillimeter'];
		}

		return array( $minTemperature, $maxTemperature, $maxWindSpeed, $sumSunshine, $sumRain );
    }

    // https://www.amcharts.com/free-animated-svg-weather-icons/

    // https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    // precipitationType
    public static function convertOctaToSVG( $datetime, $data, $timerange )
    {
        global $GLOBAL_TIMEZONE;

        $octa = $data['effectiveCloudCoverInOcta'];
        $precipitationType = $data['precipitationType'];
        $precipitationProbabilityInPercent = $data['precipitationProbabilityInPercent'];
        $precipitationAmountInMillimeter = $data['precipitationAmountInMillimeter'];

        $thunderstormProbabilityInPercent = $data['thunderstormProbabilityInPercent'];
        $freezingRainProbabilityInPercent = $data['freezingRainProbabilityInPercent'];
        $hailProbabilityInPercent = $data['hailProbabilityInPercent'];
        $snowfallProbabilityInPercent = $data['snowfallProbabilityInPercent'];

        $time = $datetime->format("U");

        $sun_info = date_sun_info($time, explode(",",LOCATION)[0], explode(",",LOCATION)[1]);
        $sunrise = DateTime::createFromFormat('U', $sun_info["sunrise"]);
        $sunrise->setTimezone($GLOBAL_TIMEZONE);
        $sunset = DateTime::createFromFormat('U', $sun_info["sunset"]);
        $sunset->setTimezone($GLOBAL_TIMEZONE);

        //echo $datetime->format("H:i:s").":".$sunrise->format("H:i:s").":" . ($datetime < $sunrise) . ":<br>";
        //echo $datetime->format("H:i:s").":".$sunset->format("H:i:s").":" . ($datetime > $sunset) . ":<br>";

		// https://de.wikipedia.org/wiki/Bew%C3%B6lkung
		// 0-8 + 9
        // Based on Cloudiness
        if( $octa >= 6 ) $index = 4;
        else if( $octa > 4.5 ) $index = 3;
        else if( $octa > 3.0 ) $index = 2;
        else if( $octa > 1.5 ) $index = 1;
        else $index = 0;

        $minutes_to_add = ( $timerange / 2 * 60);
        $ref_datetime = $datetime->add(new DateInterval('PT' . $minutes_to_add . 'M'));
        $isNight = ( $ref_datetime < $sunrise || $ref_datetime > $sunset );

        $icon = Weather::$sunConfig[ $isNight ? 'night' : 'day' ][$index];

        if( $precipitationProbabilityInPercent > 30 && $precipitationAmountInMillimeter > 0 )
        {
            //error_log( $timerange . " " . $precipitationAmountInMillimeter );

            if( $timerange == 24 )
            {
                if( $precipitationAmountInMillimeter > 4 ) $amount = 4;
                else if( $precipitationAmountInMillimeter > 2 ) $amount = 3;
                else if( $precipitationAmountInMillimeter > 1 ) $amount = 2;
                else $amount = 1;
            }
            else if( $timerange == 3 )
            {
                if( $precipitationAmountInMillimeter > 3 ) $amount = 4;
                else if( $precipitationAmountInMillimeter > 2 ) $amount = 3;
                else if( $precipitationAmountInMillimeter > 1 ) $amount = 2;
                else $amount = 1;
            }
            else
            {
                if( $precipitationAmountInMillimeter > 1.3 ) $amount = 4;
                else if( $precipitationAmountInMillimeter > 0.9 ) $amount = 3;
                else if( $precipitationAmountInMillimeter > 0.5 ) $amount = 2;
                else $amount = 1;
            }

            $rain_type = ( $freezingRainProbabilityInPercent > 10 || $hailProbabilityInPercent > 10 || $snowfallProbabilityInPercent > 10 ) ? 'snowflake' : 'raindrop';
            $rain_type .= $amount;
        }
        else
        {
            $rain_type = 'none';
        }

        if( $thunderstormProbabilityInPercent > 5 )
        {
            $thunder_type = "thunder";
        }
        else
        {
            $thunder_type = 'none';
        }

        return file_get_contents('icons/svg/' . $icon  . '_' . $rain_type . '_' . $thunder_type . '_grayscaled.svg');
        //return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" style="height:100%;width:100%">
        //            <use href="/static/shared/icons/weather/svg/' . $icon  . '_' . $rain_type . '_' . $thunder_type . '_grayscaled.svg#' . $icon  . '_' . $rain_type . '_' . $thunder_type . '" />
        //        </svg>';
    }

    public static function getSVG( $icon, $id)
    {
        return file_get_contents('icons/svg/' . $id . '.svg');
    }

    public static function formatDuration($duration)
    {
        if( $duration < 180 ) return $duration . " min.";
        return round( $duration / 60 ) . " h";
    }
    
    public static function formatHour($datetime)
    {
        return $datetime->format("H:i");
    }
    
    public static function formatWeekdayName($datetime)
    {
        switch( $datetime->format("N") )
        {
            case 1:
                return "Mo";
            case 2:
                return "Di";
            case 3:
                return "Mi";
            case 4:
                return "Do";
            case 5:
                return "Fr";
            case 6:
                return "Sa";
            case 7:
                return "So";
        }
    }

    public static function formatWeekdayNameLong($datetime)
    {
        switch( $datetime->format("N") )
        {
            case 1:
                return "Montag";
            case 2:
                return "Dienstag";
            case 3:
                return "Mittwoch";
            case 4:
                return "Donnerstag";
            case 5:
                return "Freitag";
            case 6:
                return "Samstag";
            case 7:
                return "Sonntag";
        }
    }

    public static function formatWeekdayDate($datetime)
    {
        return $datetime->format("d.m");
    }

    public static function formatDay($datetime)
    {
        $str = $datetime->format("d.m");
        
        if( $str == ( new DateTime() )->format("d.m") ) return "Heute (" .Weather::formatWeekdayNameLong( $datetime ) . "), " . $str;
        
        return Weather::formatWeekdayNameLong( $datetime ) . ", " . $str;
    }
}
