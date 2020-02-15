Alias /{{listener.prefix}}/listener.js "{{htdocs_path}}main/listener/{{name}}.js"
<Location /{{listener.prefix}}>
  RequestHeader unset Accept-Encoding
  AddOutputFilterByType SUBSTITUTE text/html
  Substitute "s|<head([^>]*)>|<head$1><script src=\"/{{listener.prefix}}/listener.js\"></script>|i"
</Location>
<Location "/{{listener.prefix}}/listener.js">
  ProxyPass !
</Location>
 
 
