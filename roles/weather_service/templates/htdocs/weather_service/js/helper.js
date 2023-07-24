mx.WeatherHelper = (function( ret ) {
    ret.formatWeekdayDate = function(datetime)
    {
        return mx.WeatherHelper.formatLeadingZero(datetime.getDate()) + "." + mx.WeatherHelper.formatLeadingZero(datetime.getMonth()+1);
    }

    ret.formatWeekdayName = function(datetime)
    {
        switch( datetime.getDay() )
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
            case 0:
                return "So";
        }
    }

    ret.formatWeekdayNameLong = function(datetime)
    {
        switch( datetime.getDay() )
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
            case 0:
                return "Sonntag";
        }
    }

    ret.formatLeadingZero = function(number)
    {
        if( number < 10 ) return "0" + number;
        return number;
    }

    ret.formatHour = function(datetime)
    {
        return mx.WeatherHelper.formatLeadingZero( datetime.getHours() ) + ":" + mx.WeatherHelper.formatLeadingZero( datetime.getMinutes() );
    }

    ret.formatDay = function(datetime)
    {
        let now = new Date()
        let str = mx.WeatherHelper.formatLeadingZero(datetime.getDate()) + "." + mx.WeatherHelper.formatLeadingZero(datetime.getMonth() + 1);

        if( now.getDate() == datetime.getDate() && now.getMonth() == datetime.getMonth() ) return "Heute (" + mx.WeatherHelper.formatWeekdayNameLong( datetime ) + "), " + str;

        return mx.WeatherHelper.formatWeekdayNameLong( datetime ) + ", " + str;
    }

    ret.formatDuration = function(duration)
    {
        if( duration < 180 ) return duration + " min.";
        return Math.round( duration / 60 ) + " h";
    }

    ret.formatNumber = function(number)
    {
        return (typeof number == 'number') ? number.toFixed(1) : number;
    }

    return ret;
})( mx.WeatherHelper || {} );
