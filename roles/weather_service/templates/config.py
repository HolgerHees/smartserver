api_username    = "{{vault_weather_api_username if vault_weather_api_username is defined else ''}}"
api_password    = "{{vault_weather_api_password if vault_weather_api_password is defined else ''}}"

db_host         = "mysql"
db_name         = "shared"
db_table        = "weather_forecast"
db_username     = "{{vault_shared_mysql_username}}"
db_password     = "{{vault_shared_mysql_password}}"

mosquitto_host  = "cloud_mosquitto"
publish_topic   = {% if publish_topic %}"{{publish_topic}}"{% else %}False{% endif %}

location        = "{{location}}"
timezone        = "{{timezone}}"

icon_path       = "/etc/weather_service/icons/svg/"
lib_path        = "/var/lib/weather_service/"
