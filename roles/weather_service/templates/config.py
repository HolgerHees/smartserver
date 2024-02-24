api_provider    = "{{weather_api_provider}}"
api_username    = {% if weather_api_username is defined %}"{{weather_api_username}}"{% else %}False{% endif %}

api_password    = {% if weather_api_password is defined %}"{{weather_api_password}}"{% else %}False{% endif %}

publish_topic   = {% if weather_mqtt_publish_topic is defined %}"{{weather_mqtt_publish_topic}}"{% else %}False{% endif %}


mosquitto_host  = "{{weather_mqtt_server}}"

db_host         = "mysql"
db_name         = "shared"
db_table        = "weather_forecast"
db_username     = "{{shared_mysql_username}}"
db_password     = "{{shared_mysql_password}}"

location        = "{{location}}"
timezone        = "{{timezone}}"

icon_path       = "/opt/weather_service/icons/svg/"
lib_path        = "/var/lib/weather_service/"
