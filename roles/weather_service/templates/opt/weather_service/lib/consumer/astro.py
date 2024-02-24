import logging
from datetime import datetime, timedelta
import schedule

from lib.helper.forecast import WeatherHelper


class AstroConsumer():
    '''Handler client'''
    def __init__(self, config, handler):
        self.is_running = False

        self.handler = handler

        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.astroSunrise = None;
        self.astroSunset = None;

    def start(self):
        self.is_running = True

        self._initData()

        schedule.every().hour.at("00:00").do(self.refresh)

    def terminate(self):
        self.is_running = False

    def _initData(self):
        activeDay = datetime.now()
        activeDay = activeDay.replace(hour=0, minute=0, second=0, microsecond=0)
        activeTimestamp = datetime.timestamp(activeDay)

        sunrise, sunset = WeatherHelper.getSunriseAndSunset(self.latitude, self.longitude)
        self.astroSunrise = sunrise.isoformat()
        self.astroSunset = sunset.isoformat()

    def refresh(self):
        self._initData()

        self.handler.notifyChangedAstroData("astroSunrise", self.astroSunrise)
        self.handler.notifyChangedAstroData("astroSunset", self.astroSunset)

    def getValues(self):
        return { "astroSunrise": self.astroSunrise, "astroSunset": self.astroSunset }

    def getStateMetrics(self):
        return ["weather_service_state{{type=\"consumer_astro\",group=\"running\"}} {}".format(1 if self.is_running else 0)]
