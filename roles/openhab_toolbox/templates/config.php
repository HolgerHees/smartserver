<?php

class Setup
{
    public static function getTimezone()
    {
        return new DateTimezone( 'Europe/Berlin' );
    }
    
	public static function getOpenHabMysql()
	{
		return new DBConnectorOpenhab( "127.0.0.1", "{{openhab_mysql_username}}", "{{openhab_mysql_password}}", "openhab" );
	}
	
	public static function getOpenHabInfluxDB()
	{
		return new DBConnectorInflux( "127.0.0.1", "8086", "{{openhab_influxdb_username}}", "{{openhab_influxdb_password}}", "openhab_db" );
	}
	
	public static function getOpenHabRest()
	{
		return new RestConnectorOpenhab( "127.0.0.1", "8080" );
	}
}
 
