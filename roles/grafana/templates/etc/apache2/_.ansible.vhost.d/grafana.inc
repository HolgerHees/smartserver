<Location />
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule /api/live/(.*) ws://grafana:3000/api/live/$1 [P,L]

  ProxyPass http://grafana:3000/
  ProxyPassReverse http://grafana:3000/
  RequestHeader set Authorization "Basic {{ (vault_grafana_app_username + ':' + vault_grafana_app_password) | b64encode }}"
</Location>

