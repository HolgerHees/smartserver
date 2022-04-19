RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*) ws://speedtest:80/$1 [P,L]

<Location />
  ProxyPass http://speedtest:80/
  ProxyPassReverse http://speedtest:80/
</Location>

RemoteIPHeader X-Forwarded-For
