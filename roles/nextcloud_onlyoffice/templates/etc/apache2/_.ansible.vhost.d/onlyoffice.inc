<Location />
  ProxyPass http://127.0.0.1:9080/
  ProxyPreserveHost on
  RequestHeader set X-Forwarded-Proto "https" env=HTTPS
</Location>
