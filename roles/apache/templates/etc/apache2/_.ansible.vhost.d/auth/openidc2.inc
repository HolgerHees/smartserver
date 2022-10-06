Alias /_auth/invalid/ "{{htdocs_path}}_auth/invalid.html"
Alias /_auth/relogin/ "{{htdocs_path}}_auth/relogin.html"
Alias /_auth/ "{{htdocs_path}}_auth/"

<Location "/_auth/">
    ProxyPass !
    Require all granted
</Location>

<Location "/_auth/retry/">
    RewriteRule .* /redirect_uri?logout=/ [R,L]
</Location>

<Location "/_auth/logout/">
    RewriteRule .* /redirect_uri?logout=/_auth/relogin/ [R,L]
</Location>

<Location "/_auth/relogin/">
    Header add Set-Cookie "openidc_supported=1;Path=/;Max-Age=2;"

    Header unset ETag
    Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate"
    #Header set Pragma "no-cache"
    #Header set Expires "Wed, 12 Jan 1980 05:00:00 GMT"
</Location>
