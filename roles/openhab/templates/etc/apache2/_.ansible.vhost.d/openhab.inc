Alias /toolbox "{{htdocs_path}}toolbox"

# forced http1 is needed for openhab app on android. Soemtimes is stucks with http2 enabled
Protocols http/1.1
ProtocolsHonorOrder Off

<Location />
  # When Upgrade:websocket header is present, redirect to ws
  # Using NC flag (case-insensitive) as some browsers will pass Websocket
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule ^/rest/(.*) ws://127.0.0.1:8080/rest/$1 [P,L]

  ProxyPass http://127.0.0.1:8080/
  ProxyPreserveHost on
  RequestHeader set X-Forwarded-Proto "https" env=HTTPS
</Location>

<Location /basicui/manifest.json>
  Require all granted
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
