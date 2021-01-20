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

    #RewriteEngine On
    #RewriteCond %{REQUEST_METHOD} POST
    #RewriteCond %{REQUEST_URI} ^/index\.php/apps/user_saml/saml/login.*
    #RewriteRule ^(.*)$ $1 [QSA,L]
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

#<LocationMatch "^/index\.php/apps/user_saml/saml/login.*">
#    <If "%{REQUEST_METHOD} =~ /^POST/">
#    Redirect "%{REQUEST_URL}?%{QUERY_STRING}"
#    </If>
#</LocationMatch>

Header always unset X-Frame-Options
Header always edit Content-Security-Policy "frame-ancestors 'self'" "frame-ancestors {{server_domain}} *.{{server_domain}}"

# fix for not submitted strict same site cookies during redirects
SetEnvIf Cookie "(.*nc_sameSiteCookielax=.*)" SAME_SITE_COOKIE=$1
RequestHeader set Cookie "%{SAME_SITE_COOKIE}e;__Host-nc_sameSiteCookiestrict=true;" env=SAME_SITE_COOKIE
