import logging
from datetime import datetime, timedelta

from lib.helper.forecast import WeatherHelper


class AstroConsumer():
    '''Handler client'''
    def __init__(self, config):
        self.is_running = False

        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

    def start(self):
        self.is_running = True

    def terminate(self):
        self.is_running = False

    def getValues(self, last_modified, requested_fields = None ):
        result = {}
        _last_modified = last_modified

        activeDay = datetime.now()
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
        activeTimestamp = datetime.timestamp(activeDay)

        if last_modified < activeTimestamp:
            sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude)

            _last_modified = activeTimestamp
            if "astroSunrise" in requested_fields:
                result["astroSunrise"] = sunrise.isoformat()
            if "astroSunset" in requested_fields:
                result["astroSunset"] = sunset.isoformat()

        return [result, _last_modified]

    #def getLastModified(self, last_modified, requested_fields = None ):
    #    _last_modified = last_modified
    #    return _last_modified

    def getStateMetrics(self):
        return ["weather_service_state{{type=\"consumer_astro\",group=\"running\"}} {}".format(1 if self.is_running else 0)]
