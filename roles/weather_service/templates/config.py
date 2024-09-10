api_provider    = "{{weather_api_provider}}"
api_username    = {% if weather_api_username is defined %}"{{weather_api_username}}"{% else %}False{% endif %}

api_password    = {% if weather_api_password is defined %}"{{weather_api_password}}"{% else %}False{% endif %}

mosquitto_host  = "{{weather_mqtt_server}}"

publish_provider_topic   = {% if weather_mqtt_publish_provider_topic is defined %}"{{weather_mqtt_publish_provider_topic}}"{% else %}False{% endif %}


station_consumer_topic   = {% if weather_mqtt_station_consumer_topic is defined %}"{{weather_mqtt_station_consumer_topic}}"{% else %}False{% endif %}


db_host         = "mariadb"
db_name         = "shared"
db_table        = "weather_forecast"
db_username     = "{{shared_mariadb_username}}"
db_password     = "{{shared_mariadb_password}}"

location        = "{{location}}"
timezone        = "{{timezone}}"

icon_path       = "/opt/weather_service/icons/svg/"
lib_path        = "/var/lib/weather_service/"
