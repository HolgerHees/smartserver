RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*) ws://openclaw:18789/$1 [P,L]

<Location />
  ProxyPass http://openclaw:18789/
  ProxyPassReverse http://openclaw:18789/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
</Location>

