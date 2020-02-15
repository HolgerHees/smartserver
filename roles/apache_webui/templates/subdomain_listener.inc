Alias /listener.js "{{htdocs_path}}main/listener/{{name}}.js"
<Location />
  RequestHeader unset Accept-Encoding
  AddOutputFilterByType SUBSTITUTE text/html
  Substitute "s|<head([^>]*)>|<head$1><script src=\"/listener.js\"></script>|i"
</Location>
<Location "/listener.js">
  ProxyPass !
</Location>
 
