FROM alpine:{{alpine_version}}

RUN apk update && apk upgrade &&  apk --update --no-cache add python3 py3-paho-mqtt py3-requests py3-tz py3-mysqlclient

#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/usr/bin/python3","/etc/weather_forecast/daemon.py"]

