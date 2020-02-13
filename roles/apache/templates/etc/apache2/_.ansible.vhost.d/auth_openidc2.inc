Alias /auth/invalid/ "{{htdocs_path}}auth/invalid.html"
Alias /auth/relogin/ "{{htdocs_path}}auth/relogin.html"
Alias /auth/ "{{htdocs_path}}auth/"

<Location "/auth/">
    ProxyPass !
    Require all granted
</Location>

<Location "/auth/retry/">
    RewriteRule .* /redirect_uri?logout=/ [R,L]
</Location>

<Location "/auth/logout/">
    RewriteRule .* /redirect_uri?logout=/auth/relogin/ [R,L]
</Location>

<Location "/auth/relogin/">
    Header add Set-Cookie "openidc_supported=1;Path=/;Max-Age=2;"

    Header unset ETag
    Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate"
    #Header set Pragma "no-cache"
    #Header set Expires "Wed, 12 Jan 1980 05:00:00 GMT"
</Location>
