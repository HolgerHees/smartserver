#SetEnvIf Host "^(.*)$" THE_HOST=$1
#RequestHeader setifempty X-Forwarded-Proto https
#RequestHeader setifempty X-Forwarded-Host %{THE_HOST}e
#X-Forwarded-For $proxy_add_x_forwarded_for;
#ProxyAddHeaders Off

#RewriteCond %{HTTP:Connection} Upgrade [NC]
#RewriteCond %{HTTP:Upgrade} websocket [NC]
#RewriteRule /(.*)(\/cool)$ ws://libreoffice:9980/$1$2 [P,L]

AllowEncodedSlashes NoDecode
ProxyPreserveHost On

# static html, js, images, etc. served from coolwsd
# browser is the client part of Collabora Online
ProxyPass           /browser http://libreoffice:9980/browser retry=0
ProxyPassReverse    /browser http://libreoffice:9980/browser

# WOPI discovery URL
ProxyPass           /hosting/discovery http://libreoffice:9980/hosting/discovery retry=0
ProxyPassReverse    /hosting/discovery http://libreoffice:9980/hosting/discovery

# Capabilities
ProxyPass           /hosting/capabilities http://libreoffice:9980/hosting/capabilities retry=0
ProxyPassReverse    /hosting/capabilities http://libreoffice:9980/hosting/capabilities

# Main websocket
ProxyPassMatch      "/cool/(.*)/ws$"      ws://libreoffice:9980/cool/$1/ws nocanon

# Admin Console websocket
ProxyPass           /cool/adminws ws://libreoffice:9980/cool/adminws

# Download as, Fullscreen presentation and Image upload operations
ProxyPass           /cool http://libreoffice:9980/cool
ProxyPassReverse    /cool http://libreoffice:9980/cool

# Compatibility with integrations that use the /lool/convert-to endpoint
ProxyPass           /lool http://libreoffice:9980/cool
ProxyPassReverse    /lool http://libreoffice:9980/cool

Header edit Content-Security-Policy "frame-ancestors" "frame-ancestors libreoffice.{{server_domain}}:* nextcloud.{{server_domain}}:* {{server_domain}}:*"
