RewriteCond %{HTTP:Connection} Upgrade [NC]
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteRule /(.*) ws://frigate:5000/$1 [P,L]

#LoadModule dumpio_module modules/mod_dumpio.so
#DumpIOInput On
#DumpIOOutput On
#LogLevel dumpio:trace7

<Location />
  ProxyPass http://frigate:5000/
  ProxyPassReverse http://frigate:5000/

  RequestHeader set X-Forwarded-Userrole "admin" "expr=%{ENV:REMOTE_USERGROUP} =~ m#^.*admin.*$#"
  RequestHeader set X-Forwarded-Userrole "viewer" "expr=%{ENV:REMOTE_USERGROUP} !~ m#^.*admin.*$#"

  RequestHeader unset Origin
  RequestHeader unset Referer
  RequestHeader unset Authorization
</Location>

