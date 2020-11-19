#SetEnvIf Host "^(.*)$" THE_HOST=$1
RequestHeader setifempty X-Forwarded-Proto https
#RequestHeader setifempty X-Forwarded-Host %{THE_HOST}e
#X-Forwarded-For $proxy_add_x_forwarded_for;
#ProxyAddHeaders Off

ProxyPassMatch (.*)(\/websocket)$ "ws://onlyoffice/$1$2"
ProxyPass / "http://onlyoffice/"
ProxyPassReverse / "http://onlyoffice/"
