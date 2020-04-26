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

#https://docs.nextcloud.com/server/11/admin_manual/configuration_server/sso_configuration.html#configuring-environment-based-authentication
#<LocationMatch "^(?!/(?:redirect_uri|index\.php/login$)).+">
#    Require all granted
#</LocationMatch>

<LocationMatch "^/status\.php|^/index.php/login/flow|^/index.php/apps/theming/|^\/(?!remote).*\.css?|^\/(?!remote).*\.js?|^\/(?!remote).*\.svg|/js/accessibility">
    Require all granted
</LocationMatch>
#<LocationMatch "^/status.php|^/index.php/login/flow|^/index.php/apps/theming/manifest">
#    Require all granted
#</LocationMatch>

<LocationMatch "^/index.php/apps/onlyoffice/.+">
    Require all granted
</LocationMatch>

Header always unset X-Frame-Options
Header always edit Content-Security-Policy "frame-ancestors 'self'" "frame-ancestors {{server_domain}} *.{{server_domain}}"

# fix for not submitted strict same site cookies during redirects
SetEnvIf Cookie "(.*nc_sameSiteCookielax=.*)" SAME_SITE_COOKIE=$1
RequestHeader set Cookie "%{SAME_SITE_COOKIE}e;__Host-nc_sameSiteCookiestrict=true;" env=SAME_SITE_COOKIE
