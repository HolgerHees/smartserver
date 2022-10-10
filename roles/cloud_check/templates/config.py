mosquitto_host  = "cloud_mosquitto"

peer_name = "{{cloud_vpn.name}}"

cloud_peers = {
{% for peer in cloud_vpn.peers %}
  "{{peer}}": { "host": "{{cloud_vpn.peers[peer].host}}", "email": "{{cloud_vpn.peers[peer].notification_email}}" },
{% endfor %}
}
