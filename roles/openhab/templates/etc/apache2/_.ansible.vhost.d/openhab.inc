Alias /weather "{{htdocs_path}}weather"

<Location />
  # When Upgrade:websocket header is present, redirect to ws
  # Using NC flag (case-insensitive) as some browsers will pass Websocket
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule ^/rest/(.*) ws://openhab:8080/rest/$1 [P,L]

  ProxyPass http://openhab:8080/
  ProxyPassReverse http://openhab:8080/
  RequestHeader set X-Forwarded-Proto "https" env=HTTPS
  
  Header add Set-Cookie "X-OPENHAB-AUTH-HEADER=true;path=/;Secure"
  RequestHeader unset Authorization
</Location>

<Location /basicui/manifest.json>
  Require all granted
</Location>

<Location /weather>
  ProxyPass !
</Location>

<Location /loki>
  ProxyPass http://loki:3100 retry=0
  ProxyPassReverse http://loki:3100
</Location>

<Location /grafana>
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule /api/live/(.*) ws://grafana:3000/api/live/$1 [P,L]
  
  ProxyPass http://grafana:3000
  ProxyPassReverse http://grafana:3000
  RequestHeader unset Authorization
  RequestHeader set X-WEBAUTH-USER "{{vault_grafana_app_username}}"
</Location>

<Location /api/v1/settings/notifications>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>

<Location /habpanel/vendor/aCKolor.min.js.map>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>
