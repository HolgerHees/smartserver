api_provider    = "{{weather_api_provider}}"
api_username    = {% if vault_weather_api_username is defined %}"{{vault_weather_api_username}}"{% else %}False{% endif %}

api_password    = {% if vault_weather_api_password is defined %}"{{vault_weather_api_password}}"{% else %}False{% endif %}

publish_topic   = {% if weather_mqtt_publish_topic is defined %}"{{weather_mqtt_publish_topic}}"{% else %}False{% endif %}


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
