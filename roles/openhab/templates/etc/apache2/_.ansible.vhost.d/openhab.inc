RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*) ws://openhab:8080/$1 [P,L]

ProxyTimeout 3000
RemoteIPHeader X-Forwarded-For

<Location />
  ProxyPass http://openhab:8080/
  ProxyPassReverse http://openhab:8080/
  
  Header add Set-Cookie "X-OPENHAB-AUTH-HEADER=true;path=/;Secure"

  ProxyPreserveHost On
  
  RequestHeader set X-Forwarded-Proto "https" env=HTTPS
  RequestHeader unset Authorization
</Location>

<Location /basicui/manifest.json>
  Require all granted
</Location>

<Location /loki>
  ProxyPass http://loki:3100 retry=0
  ProxyPassReverse http://loki:3100
</Location>

<Location /api/v1/settings/notifications>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>

<Location /habpanel/vendor/aCKolor.min.js.map>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>
