var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('weather', 100, '{i18n_Weatherforecast}', 'weather_forecast.svg');
subGroup.addUrl('weather', '//openhab.{host}/weather/weatherDetailOverview.php', 'user', 1000, '{i18n_Weatherforecast}', '{i18n_Meteo Group}', false);
