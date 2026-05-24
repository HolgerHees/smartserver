<Location />
  ProxyPreserveHost On
  ProxyErrorOverride      Off

  Header edit Set-Cookie "SameSite=Strict" "SameSite=Lax"
  Header unset X-Frame-Options

  ProxyPass https://127.0.0.1:9090/ upgrade=websocket
  ProxyPassReverse https://127.0.0.1:9090/
</Location>

