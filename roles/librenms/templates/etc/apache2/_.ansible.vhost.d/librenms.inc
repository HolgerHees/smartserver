<Location />
  ProxyPass http://librenms:8000/
  ProxyPassReverse http://librenms:8000/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
  
  RequestHeader unset Authorization
  RequestHeader set "X-Remote-User" "librenms"
  RequestHeader set "X-Auth-Token" "{{librenms_api_token}}"
</Location>

