<?php
define("DB_HOST","mysql");
define("DB_NAME","shared");
define("DB_TABLE","weather_forecast");
define("DB_USERNAME","{{vault_shared_mysql_username}}");
define("DB_PASSWORD",'{{vault_shared_mysql_password}}');

define("LOCATION",'{{location}}');

date_default_timezone_set('{{timezone}}');

$GLOBAL_TIMEZONE = new DateTimezone(date_default_timezone_get());
