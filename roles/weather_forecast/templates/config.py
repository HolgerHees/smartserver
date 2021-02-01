api_username    = "{{vault_weather_api_username}}"
api_password    = "{{vault_weather_api_password}}"

db_host         = "mysql"
db_name         = "shared"
db_table        = "weather_forecast"
db_username     = "{{vault_shared_mysql_username}}"
db_password     = "{{vault_shared_mysql_password}}"

mosquitto_host  = "cloud_mosquitto"
publish_topic   = {% if publish_topic is defined and publish_topic %}"{{publish_topic}}"{% else %}False{% endif %}


location        = "{{location}}"
timezone        = "{{timezone}}"
