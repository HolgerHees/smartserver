<?php

class Weather
{
    private static $sunConfig = array(
        // possible icons and typeIconOffsetLeft
        'day' => array( 'day', 'cloudy-day-0', 'cloudy-day-1', 'cloudy-day-2', 'cloudy' ),
        'night' => array( 'night', 'cloudy-night-0', 'cloudy-night-1', 'cloudy-night-2', 'cloudy'	),
		
		'typeIconOffsetLeft' => array( 
			'day' => 25, 'cloudy-day-0' => 37, 'cloudy-day-1' => 28, 'day_default' => 20,
			'night' => 25, 'cloudy-night-0' => 6, 'cloudy-night-1' => 8, 'night_default' => 22,
			'cloudy' => 18,
		),
		'typeIconOffsetTop' => array(
			'raindrop' => array( 'day' => 57, 'night' => 57, 'default' => 55 ),
			'snowflake' => array( 'day' => 57, 'night' => 57, 'default' => 55 ),
			'thunder' => array( 'day' => 36, 'night' => 36, 'default' => 36 ),
		),
        
        //'snow' => array( 'snowy-1','snowy-2','snowy-3','snowy-4','snowy-5','snowy-6' ),
        //'rain' => array( 'rainy-1','rainy-2','rainy-3','rainy-4','rainy-5','rainy-6','rainy-7' ),
        //'other' => array( 'thunder' ),
        
        'scale' => array(
			// size, top, left
            array( array( "100", "0", "0" ), array( 'cloudy-day-0','cloudy-day-1','cloudy-day-2','cloudy-day-3' ) ),
            array( array( "100", "0", "0" ), array( 'cloudy-night-0','cloudy-night-1','cloudy-night-2','cloudy-night-3' ) ),
            array( array( "100", "0", "0" ), array( 'cloudy' ) ),
            array( array( "80", "10", "-3" ), array( 'day' ) ),
            array( array( "60", "20", "5" ), array( 'night' ) )
        )
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
        if( $current_value['precipitationProbabilityInPercent'] < $hourlyData['precipitationProbabilityInPercent'] )
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
    public static function convertOctaToSVG( $datetime, $data, $timerange, $theme = "colored" )
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
        
        $sunrise = DateTime::createFromFormat('U', date_sunrise($time, SUNFUNCS_RET_TIMESTAMP, 52.34772, 13.62140, 96, 1));
        $sunrise->setTimezone($GLOBAL_TIMEZONE);
        $sunset = DateTime::createFromFormat('U', date_sunset($time, SUNFUNCS_RET_TIMESTAMP, 52.34772, 13.62140, 96, 1));
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
        
        $hour = $datetime->format("H");
        $isNight = ( $datetime < $sunrise || $datetime->format("H") <= 5 || $datetime > $sunset );
        $icon = Weather::$sunConfig[ $isNight ? 'night' : 'day' ][$index];
    
        //$index = round( $octa / ( 9 / count($possible_icons) ) );

        $svg = '';
        
        $typeLeftOffset = isset( Weather::$sunConfig['typeIconOffsetLeft'][$icon] ) ? Weather::$sunConfig['typeIconOffsetLeft'][$icon] : Weather::$sunConfig['typeIconOffsetLeft'][ ( $isNight ? 'night' : 'day' ) . '_default'];
        
        if( $precipitationProbabilityInPercent > 10 && $precipitationAmountInMillimeter > 0 )
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
        
            
            $type = ( $freezingRainProbabilityInPercent > 10 || $hailProbabilityInPercent > 10 || $snowfallProbabilityInPercent > 10 ) ? 'snowflake' : 'raindrop';

			$typeTopOffset = isset( Weather::$sunConfig['typeIconOffsetTop'][$type][$icon] ) ? Weather::$sunConfig['typeIconOffsetTop'][$type][$icon] : Weather::$sunConfig['typeIconOffsetTop'][$type]['default'];

            $svg .= '<div class="'.$type.'_background_' . $amount . ' raindrop_snowflake_background" style="left:'.$typeLeftOffset.'%;top:'.$typeTopOffset.'%"></div>';
			$svg .= '<svg style="left:'.$typeLeftOffset.'%;top:'.$typeTopOffset.'%" class="'.$type.'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
                    <use href="/static/shared/habpanel/svg/icons.svg#self_'.$type.$amount.'_grayscaled" />
                 </svg>';
        }
        
        if( $thunderstormProbabilityInPercent > 2 )
        {
			$type = "thunder";
			$level = ( $thunderstormProbabilityInPercent > 5 ) ? " strong" : "";
			
			$typeTopOffset = isset( Weather::$sunConfig['typeIconOffsetTop'][$type][$icon] ) ? Weather::$sunConfig['typeIconOffsetTop'][$type][$icon] : Weather::$sunConfig['typeIconOffsetTop'][$type]['default'];

			$svg .= '<svg style="left:'.$typeLeftOffset.'%;top:'.$typeTopOffset.'%" class="'.$type.$level.'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
                    <use href="/static/shared/habpanel/svg/icons.svg#self_'.$type.'_grayscaled" />
                 </svg>';
        }
        
        $svg = Weather::getSunSVG($icon,$theme) . $svg;
        
        return $svg;
    }

    public static function getSunSVG( $icon, $theme = "light" )
    {
        $style = "";
        foreach( Weather::$sunConfig['scale'] as $_scale => $_data )
        {
            if( in_array( $icon, $_data[1] ) )
            {
                $style = " style=\"margin-top: ".($_data[0][1])."%;margin-left: ".$_data[0][2]."%;height: ".$_data[0][0]."%; width: ".$_data[0][0]."%;\"";
                break;
            }
        }
        
        return Weather::getSVG( $icon, 'self_' . $icon . '_grayscaled' , $style );
    }

    public static function getSVG( $icon, $id, $style = "" )
    {
        return '<svg'.$style.' class="' . $icon . '" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
                    <use href="/static/shared/habpanel/svg/icons.svg#'.$id.'" />
                </svg>';
    }

    public static function formatDuration($duration)
    {
        if( $duration < 180 ) return $duration . " min.";
        return gmdate("H", $duration * 60 ) . " h";
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
