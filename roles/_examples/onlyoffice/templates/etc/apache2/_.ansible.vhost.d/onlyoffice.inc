#SetEnvIf Host "^(.*)$" THE_HOST=$1
RequestHeader setifempty X-Forwarded-Proto https
#RequestHeader setifempty X-Forwarded-Host %{THE_HOST}e
#X-Forwarded-For $proxy_add_x_forwarded_for;
#ProxyAddHeaders Off

RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*)(\/websocket)$ ws://onlyoffice/$1$2 [P,L]

ProxyPass / "http://onlyoffice/"
ProxyPassReverse / "http://onlyoffice/"
