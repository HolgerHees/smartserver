Alias /toolbox "{{htdocs_path}}toolbox"

<Location />
  ProxyPass http://127.0.0.1:8080/
  ProxyPreserveHost on
  RequestHeader set X-Forwarded-Proto "https" env=HTTPS
</Location>

<Location /toolbox>
  ProxyPass !
</Location>

<Location /elasticsearch>
  ProxyPreserveHost On
  ProxyPass http://127.0.0.1:9200 retry=0
  ProxyPassReverse http://127.0.0.1:9200
</Location>

<Location /grafana>
  ProxyPreserveHost On
  ProxyPass http://127.0.0.1:3000
  ProxyPassReverse http://127.0.0.1:3000
  RequestHeader set Authorization "Basic YWRtaW46YWRtaW4="
</Location>

<Location /api/v1/settings/notifications>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>

<Location /habpanel/vendor/aCKolor.min.js.map>
  RewriteRule ^(.*)$ $1 [R=204,L]
</Location>
