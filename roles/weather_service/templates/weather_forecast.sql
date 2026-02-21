SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

CREATE TABLE `weather_forecast` (
  `datetime` datetime NOT NULL,
  `airTemperatureInCelsius` decimal(10,1) NOT NULL,
  `feelsLikeTemperatureInCelsius` decimal(10,1) NOT NULL,
  `relativeHumidityInPercent` smallint(6) NOT NULL,
  `windSpeedInKilometerPerHour` decimal(10,1) NOT NULL,
  `windDirectionInDegree` smallint(6) NOT NULL,
  `windGustInKilometerPerHour` decimal(10,1) NOT NULL,
  `cloudCoverInOcta` decimal(10,1) NOT NULL,
  `thunderstormProbabilityInPercent` tinyint(4) NOT NULL,
  `freezingRainProbabilityInPercent` tinyint(4) NOT NULL,
  `hailProbabilityInPercent` tinyint(4) NOT NULL,
  `snowfallProbabilityInPercent` tinyint(4) NOT NULL,
  `precipitationProbabilityInPercent` tinyint(4) NOT NULL,
  `precipitationAmountInMillimeter` double(10,1) NOT NULL,
  `weatherCode` tinyint(4) NOT NULL,
  `uvIndex` tinyint(4) NOT NULL,
  `sunshineDurationInMinutes` smallint(6) NOT NULL,
  `directRadiationInWatt` smallint(6) NOT NULL,
  `diffuseRadiationInWatt` smallint(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

ALTER TABLE `weather_forecast`
 ADD PRIMARY KEY (`datetime`);
