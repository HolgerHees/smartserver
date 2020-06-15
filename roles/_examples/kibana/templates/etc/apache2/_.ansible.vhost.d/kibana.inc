<Location />
  ProxyPreserveHost On
  ProxyPass http://127.0.0.1:5601/ retry=0
  ProxyPassReverse http://127.0.0.1:5601/
</Location>
