<?php
class SystemConfig
{
    public static function getTimezone()
    {
        return new DateTimezone( '{{timezone}}' );
    }
    
	public static function getOpenHabMysql()
	{
		return new DBConnectorOpenhab( "mysql", "{{openhab_mysql_username}}", "{{openhab_mysql_password}}", "openhab" );
	}
	
	public static function getOpenHabInfluxDB()
	{
		return new DBConnectorInflux( "influxdb", "8086", "openhab", "{{influxdb_admin_token}}", null );
	}
	
	public static function getOpenHabRest()
	{
        // has do use the apache proxy, because openhab itself is locahost only and not reachable from inside a docker container
		return new RestConnectorOpenhab( "openhab.{{server_domain}}", "443", "https" );
	}
}
 
