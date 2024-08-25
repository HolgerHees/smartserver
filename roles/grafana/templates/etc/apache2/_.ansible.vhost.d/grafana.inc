RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /api/(.*) ws://grafana:3000/api/$1 [P,L]

<Location />
  ProxyPass http://grafana:3000/
  ProxyPassReverse http://grafana:3000/
  RequestHeader unset Authorization
</Location>

