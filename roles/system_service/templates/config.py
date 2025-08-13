internal_networks = [{% if intern_networks|length > 0 %}"{{intern_networks | join('","') }}"{% endif %}]
public_networks = [{% if public_networks|length > 0 %}"{{public_networks | join('","') }}"{% endif %}]
main_interface = "{{default_network_interface}}"
default_gateway_ip = "{{default_server_gateway}}"
default_server_network = "{{default_server_network}}"
server_name = "{{server_name}}"
server_domain = "{{server_domain}}"
server_ip = "{{default_server_ip}}"

default_isp = { {% for key in system_service_default_isp %}"{{key}}": "{{system_service_default_isp[key] | join('|')}}",{% endfor %} }

allowed_incoming_traffic = {
{% for data in system_service_allowed_incoming_traffic %}
  "{{data.target}}": { "name": "{{data.name}}", "allowed": { {% for key in data.allowed %} "{{key}}": "{{data.allowed[key] | join('|')}}", {% endfor %} }, "logs": "{{data.logs | default('')}}" },
{% endfor %}
}

traffic_blocker_enabled = {{ 'True' if system_service_traffic_blocker_enabled else 'False' }}
traffic_blocker_treshold = {
  "netflow_observed": 20,
  "netflow_scanning": 10,
  "netflow_intruded": 2,
  "apache_observed": 10,
  "apache_scanning": 5
}

netflow_enabled = {{ 'True' if system_service_netflow_collector_enabled else 'False' }}
netflow_bind_ip = {{ '"0.0.0.0"' if system_service_netflow_collector_enabled else 'None' }}
netflow_bind_port = {{ '2055' if system_service_netflow_collector_enabled else 'None' }}

service_ip = "127.0.0.1"
service_port = "8507"

librenms_token = "{% if librenms_enabled %}{{librenms_api_token}}{% endif %}"
librenms_rest = "{% if librenms_enabled %}http://librenms:8000/{% endif %}"
librenms_poller_interval = {% if librenms_enabled %}{{librenms_poller_interval | int * 60}}{% else %}0{% endif %}


openwrt_devices = {
{% for openwrt_device in openwrt_devices %}
    {% if loop.index > 1 %},{% endif %}"{{openwrt_device.host}}": {"username": "{{openwrt_device.config.openwrt.api_username}}", "password": "{{openwrt_device.config.openwrt.api_password}}" }
{% endfor %}
}

fritzbox_devices = {
{% for fritzbox_device in fritzbox_devices %}
    {% if loop.index > 1 %},{% endif %}"{{fritzbox_device.host}}": {"username": "{{fritzbox_device.config.fritzbox.api_username}}", "password": "{{fritzbox_device.config.fritzbox.api_password}}" }
{% endfor %}
}

influxdb_rest = "http://influxdb:8086"
influxdb_database = "system_info"
influxdb_token = "{{influxdb_admin_token}}"

loki_websocket = "ws://loki:3100"

mqtt_host = "mosquitto"

default_vlan = 1

startup_error_timeout = 5

remote_suspend_timeout = 300
remote_error_timeout = 900

cache_ip_dns_revalidation_interval = 900
cache_ip_mac_revalidation_interval = 900

arp_scan_interval = 60
arp_offline_timeout = 900
arp_clean_timeout = 60 * 60 * 24

openwrt_network_interval = 900
openwrt_client_interval = 60

fritzbox_network_interval = 900
fritzbox_client_interval = 60

librenms_device_interval = 900
librenms_vlan_interval = 900
librenms_fdb_interval = 300
librenms_port_interval = 60

port_scan_interval = 300
port_rescan_interval = 60*60*24

influxdb_publish_interval = 60
mqtt_republish_interval = 900

user_devices = {
{% for username in userdata %}
{% if userdata[username].phone_device is defined %}
    {% if loop.index > 1 %},{% endif %}"{{userdata[username].phone_device['ip']}}": { "type": "{{userdata[username].phone_device['type'] | default('android')}}",  "timeout": {{userdata[username].phone_device['timeout'] | default(90)}} }
{% endif %}
{% endfor %}
}

silent_device_macs = [{% if system_service_silent_device_macs|length > 0 %}"{{system_service_silent_device_macs | join('","') }}"{% endif %}]

fping_test_hosts = [ {% for host in system_service_fping_test_hosts %}"{{host}}", {% endfor %}{% if cloud_vpn is defined %}{% for peer in cloud_vpn.peers %}"{{cloud_vpn.peers[peer].host}}", {% endfor %}{% endif %} ]

speedtest_server_id = "{{system_service_speedtest_server_id}}"
