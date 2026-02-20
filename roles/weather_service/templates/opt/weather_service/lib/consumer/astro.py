from datetime import datetime, timedelta
from suntime import Sun

import logging
import schedule

from smartserver.metric import Metric


class AstroConsumer():
    '''Handler client'''
    def __init__(self, config, handler):
        self.is_running = False

        self.handler = handler

        location = config.location.split(",")
        self.latitude = float(location[0])
        self.longitude = float(location[1])

        self.sunrise = None;
        self.sunset = None;

    def start(self):
        self.is_running = True

        self.refresh()
        schedule.every().hour.at("00:00").do(self.refresh)

    def terminate(self):
        self.is_running = False

    def refresh(self):
        activeDay = datetime.now().astimezone()
        #activeTimestamp = datetime.timestamp(activeDay)

        sun = Sun(self.latitude, self.longitude)
        sunrise = sun.get_sunrise_time(activeDay, time_zone=activeDay.tzinfo).replace(year=activeDay.year, month=activeDay.month, day=activeDay.day)
        sunset = sun.get_sunset_time(activeDay, time_zone=activeDay.tzinfo).replace(year=activeDay.year, month=activeDay.month, day=activeDay.day)

        if self.sunrise != sunrise:
            self.sunrise = sunrise
            self.handler.notifyChangedAstroData("astroSunrise", self.sunrise.isoformat())
        if self.sunset != sunset:
            self.sunset = sunset
            self.handler.notifyChangedAstroData("astroSunset", self.sunset.isoformat())

    def getSunset(self):
        return self.sunset

    def getSunrise(self):
        return self.sunrise

    def getValues(self):
        return { "astroSunrise": self.sunrise.isoformat(), "astroSunset": self.sunset.isoformat() }

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("weather_service", "consumer_astro", "1" if self.is_running else "0")
        ]
