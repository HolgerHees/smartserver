<?php
class Setup
{
    public static function getTimezone()
    {
        return new DateTimezone( '{{timezone}}' );
    }
    
	public static function getOpenHabMysql()
	{
		return new DBConnectorOpenhab( "mysql", "{{vault_openhab_mysql_username}}", "{{vault_openhab_mysql_password}}", "openhab" );
	}
	
	public static function getOpenHabInfluxDB()
	{
		return new DBConnectorInflux( "influxdb", "8086", "{{vault_openhab_influxdb_username}}", "{{vault_openhab_influxdb_password}}", "openhab_db" );
	}
	
	public static function getOpenHabRest()
	{
		return new RestConnectorOpenhab( "openhab.smartmarvin.de", "443", "https" );
	}
	
	public static function getWeatherAuth()
	{
        return new GenericAuth("{{vault_weather_api_username}}","{{vault_weather_api_password}}");
	}

	public static function getGeoLocation()
	{
        $pos = explode(",","{{location}}");
        return new GeoLocation($pos[0],$pos[1]);
	}
}
 
