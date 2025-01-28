RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*) ws://frigate:5000/$1 [P,L]

<Location />
  ProxyPass http://frigate:5000/
  ProxyPassReverse http://frigate:5000/

  RequestHeader unset Origin
  RequestHeader unset Referer
  RequestHeader unset Authorization
</Location>

