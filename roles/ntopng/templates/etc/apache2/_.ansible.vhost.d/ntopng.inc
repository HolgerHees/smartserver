<Location />
  ProxyPass http://ntopng:3000/
  ProxyPassReverse http://ntopng:3000/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
</Location>

