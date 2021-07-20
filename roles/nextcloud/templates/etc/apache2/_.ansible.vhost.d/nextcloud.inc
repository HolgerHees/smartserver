DocumentRoot "{{htdocs_path}}nextcloud/"

<Directory "{{htdocs_path}}nextcloud/">
    <IfModule mod_dav.c>
      Dav off
    </IfModule>

    #SetEnvIf Request_URI ^/nextcloud/* noauth=1
    #SetEnvIf Request_URI ^/nextcloud/$ !noauth=

    #SetEnv HOME {{htdocs_path}}nextcloud/
    #SetEnv HTTP_HOME {{htdocs_path}}nextcloud/

    #Include {{htdocs_path}}nextcloud/.htaccess

    AllowOverride ALL
</Directory>

<Directory "{{htdocs_path}}nextcloud/config/">
  Require all denied
</Directory>

# should only be filter out for basic auth (ba. || ba-) domains
# for normal auth it is used by apps to submit corps token => /lib/private/AppFramework/Middleware/Security/CORSMiddleware.php
<Location "/">
    <If "%{SERVER_NAME} =~ /ba[-\.]{1}/">
    SetEnvIfNoCase Authorization "Basic.+" HTTP_AUTHORIZATION=
    </If>
</Location>

<LocationMatch "^/(?!(index\.php/apps/user_saml/saml/login.*))">
    <If "%{SERVER_NAME} !~ /ba[-\.]{1}/">
    Require all granted
    </If>
</LocationMatch>

# needs to be here, because Rewrite Rules from form and oauth authentication is disabling rewrite rules from nextcloud htaccess
RewriteCond %{HTTP_USER_AGENT} DavClnt
RewriteRule ^$ /remote.php/webdav/ [L,R=302]
RewriteRule .* - [env=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteRule ^/\.well-known/host-meta /public.php?service=host-meta [QSA,L]
RewriteRule ^/\.well-known/host-meta\.json /public.php?service=host-meta-json [QSA,L]
RewriteRule ^/\.well-known/webfinger /public.php?service=webfinger [QSA,L]
RewriteRule ^/\.well-known/nodeinfo /public.php?service=nodeinfo [QSA,L]
RewriteRule ^/\.well-known/carddav /remote.php/dav/ [R=301,L]
RewriteRule ^/\.well-known/caldav /remote.php/dav/ [R=301,L]
RewriteRule ^/remote/(.*) remote.php [QSA,L]
RewriteRule ^/(?:build|tests|config|lib|3rdparty|templates)/.* - [R=404,L]
RewriteCond %{REQUEST_URI} !^/\.well-known/(acme-challenge|pki-validation)/.*
RewriteRule ^/(?:\.|autotest|occ|issue|indie|db_|console).* - [R=404,L]

Header always unset X-Frame-Options
Header always edit Content-Security-Policy "frame-ancestors" "frame-ancestors {{server_domain}} *.{{server_domain}}"
Header always edit Content-Security-Policy "script-src" "script-src {{server_domain}}"

# fix for not submitted strict same site cookies during redirects
SetEnvIf Cookie "(.*nc_sameSiteCookielax=.*)" SAME_SITE_COOKIE=$1
RequestHeader set Cookie "%{SAME_SITE_COOKIE}e;__Host-nc_sameSiteCookiestrict=true;" env=SAME_SITE_COOKIE
