Alias /{{listener.prefix + "/" if listener.prefix is defined else ""}}listener.js "{{htdocs_path}}main/listener/{{name}}.js"
<Location /{{listener.prefix + "/" if listener.prefix is defined else ""}}>
  RequestHeader unset Accept-Encoding
  AddOutputFilterByType SUBSTITUTE text/html
  Substitute "s|<head( [^>]*)?>|<head$1><script src=\"/{{listener.prefix + "/" if listener.prefix is defined else ""}}listener.js\"></script>|i"
</Location>
<Location "/{{listener.prefix + "/" if listener.prefix is defined else ""}}listener.js">
  ProxyPass !
</Location>
 
 
