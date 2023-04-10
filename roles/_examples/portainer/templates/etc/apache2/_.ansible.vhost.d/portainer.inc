<Location />
  ProxyPass http://{{docker_portainer_ip}}:9000/
  ProxyPassReverse http://{{docker_portainer_ip}}:9000/
</Location>

