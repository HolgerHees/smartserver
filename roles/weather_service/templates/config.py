api_provider    = "{{weather_api_provider if weather_api_provider is defined else ''}}"
api_username    = "{{vault_weather_api_username if vault_weather_api_username is defined else ''}}"
api_password    = "{{vault_weather_api_password if vault_weather_api_password is defined else ''}}"
publish_topic   = {% if weather_mqtt_publish_topic %}"{{weather_mqtt_publish_topic}}"{% else %}False{% endif %}

mosquitto_host  = "{{weather_mqtt_server}}"

db_host         = "mysql"
db_name         = "shared"
db_table        = "weather_forecast"
db_username     = "{{vault_shared_mysql_username}}"
db_password     = "{{vault_shared_mysql_password}}"

location        = "{{location}}"
timezone        = "{{timezone}}"

icon_path       = "/etc/weather_service/icons/svg/"
lib_path        = "/var/lib/weather_service/"
