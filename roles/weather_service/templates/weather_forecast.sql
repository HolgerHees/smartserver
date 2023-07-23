SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

CREATE TABLE `weather_forecast` (
  `datetime` datetime NOT NULL,
  `airTemperatureInCelsius` decimal(10,1) NOT NULL,
  `feelsLikeTemperatureInCelsius` decimal(10,1) NOT NULL,
  `relativeHumidityInPercent` smallint(6) NOT NULL,
  `windSpeedInKilometerPerHour` decimal(10,1) NOT NULL,
  `windDirectionInDegree` smallint(6) NOT NULL,
  `maxWindSpeedInKilometerPerHour` decimal(10,1) NOT NULL,
  `effectiveCloudCoverInOcta` decimal(10,1) NOT NULL,
  `thunderstormProbabilityInPercent` tinyint(4) NOT NULL,
  `freezingRainProbabilityInPercent` tinyint(4) NOT NULL,
  `hailProbabilityInPercent` tinyint(4) NOT NULL,
  `snowfallProbabilityInPercent` tinyint(4) NOT NULL,
  `precipitationProbabilityInPercent` tinyint(4) NOT NULL,
  `precipitationAmountInMillimeter` double(10,1) NOT NULL,
  `precipitationType` tinyint(4) NOT NULL,
  `sunshineDurationInMinutes` smallint(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `weather_forecast`
 ADD PRIMARY KEY (`datetime`);
