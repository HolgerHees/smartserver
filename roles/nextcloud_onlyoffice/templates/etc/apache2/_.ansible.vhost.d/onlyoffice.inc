#SetEnvIf Host "^(.*)$" THE_HOST=$1
RequestHeader setifempty X-Forwarded-Proto https
#RequestHeader setifempty X-Forwarded-Host %{THE_HOST}e
#X-Forwarded-For $proxy_add_x_forwarded_for;
#ProxyAddHeaders Off

ProxyPassMatch (.*)(\/websocket)$ "ws://{{docker_onlyoffice_ip}}/$1$2"
ProxyPass / "http://{{docker_onlyoffice_ip}}/"
ProxyPassReverse / "http://{{docker_onlyoffice_ip}}/"
