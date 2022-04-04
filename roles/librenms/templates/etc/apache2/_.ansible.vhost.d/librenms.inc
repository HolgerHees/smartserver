<Location />
  ProxyPass http://localhost:8000/
  ProxyPassReverse http://localhost:8000/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
  
  RequestHeader unset Authorization
  RequestHeader set "X-Remote-User" "librenms"
  RequestHeader set "X-Auth-Token" "{{vault_librenms_api_token}}"
</Location>

