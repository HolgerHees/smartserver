internal_networks = [{% if intern_networks|length > 0 %}"{{intern_networks | join('","') }}"{% endif %}]
public_networks = [{% if public_networks|length > 0 %}"{{public_networks | join('","') }}"{% endif %}]
main_interface = "{{default_network_interface}}"
default_gateway_ip = "{{default_server_gateway}}"
default_server_network = "{{default_server_network}}"
server_name = "{{server_name}}"
server_domain = "{{server_domain}}"
server_ip = "{{default_server_ip}}"

default_isp = { {% for key in system_service_default_isp %}"{{key}}": "{{system_service_default_isp[key] | join('|')}}",{% endfor %} }

netflow_bind_ip = {{ '"0.0.0.0"' if system_service_netflow_collector else 'None' }}
netflow_bind_port = {{ '2055' if system_service_netflow_collector else 'None' }}
netflow_incoming_traffic = {
{% for data in system_service_netflow_incoming_traffic %}
  "{{data.target}}": { "name": "{{data.name}}", "allowed": { {% for key in data.allowed %} "{{key}}": "{{data.allowed[key] | join('|')}}", {% endfor %} }, "logs": "{{data.logs | default('')}}" },
{% endfor %}
}

service_ip = "127.0.0.1"
service_port = "8507"

librenms_token = "{% if librenms_devices|length > 0 %}{{librenms_api_token if librenms_api_token is defined else ''}}{% endif %}"
librenms_rest = "{% if librenms_devices|length > 0 %}http://librenms:8000/api/v0/{% endif %}";
librenms_poller_interval = {{librenms_poller_interval | int * 60}}

openwrt_username = "{% if openwrt_devices|length > 0 %}{{system_service_openwrt_api_username | default('')}}{% endif %}"
openwrt_password = "{% if openwrt_devices|length > 0 %}{{system_service_openwrt_api_password | default('')}}{% endif %}"
openwrt_devices = [{% if openwrt_devices|length > 0 %}"{{openwrt_devices | map(attribute='host') | list | join('","') }}"{% endif %}]

fritzbox_username = "{% if fritzbox_devices|length > 0 %}{{system_service_fritzbox_api_username}}{% endif %}"
fritzbox_password = "{% if fritzbox_devices|length > 0 %}{{system_service_fritzbox_api_password}}{% endif %}"
fritzbox_devices = [{% if fritzbox_devices|length > 0 %}"{{fritzbox_devices | map(attribute='host') | list | join('","') }}"{% endif %}]

switch_uplinks = {
{% for system_service_device in system_service_devices %}
{% if system_service_device.config.system_service.switch_uplink is defined %}
    {% if loop.index > 1 %},{% endif %}"{{system_service_device.host}}": "{{system_service_device.config.system_service.switch_uplink}}"
{% endif %}
{% endfor %}
}

influxdb_rest = "http://influxdb:8086"
influxdb_database = "system_info"
influxdb_token = "{{influxdb_admin_token}}"

loki_websocket = "ws://loki:3100"

mqtt_host = "mosquitto"

traffic_blocker_enabled = {{ 'True' if system_service_traffic_blocker and system_service_netflow_incoming_traffic | length > 0 else 'False' }}
traffic_blocker_treshold = {
  "netflow_observed": 20,
  "netflow_scanning": 10,
  "netflow_intruded": 2,
  "apache_observed": 10,
  "apache_scanning": 5
}

default_vlan = 1

startup_error_timeout = 5

remote_suspend_timeout = 300
remote_error_timeout = 900

cache_ip_dns_revalidation_interval = 900
cache_ip_mac_revalidation_interval = 900

arp_scan_interval = 60
arp_soft_offline_device_timeout = 60
arp_hard_offline_device_timeout = 900
arp_clean_device_timeout = 60 * 60 * 24 * 7

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

fping_test_hosts = [ {% for host in system_service_fping_test_hosts %}"{{host}}", {% endfor %}{% if cloud_vpn is defined %}{% for peer in cloud_vpn.peers %}"{{cloud_vpn.peers[peer].host}}", {% endfor %}{% endif %} ]

speedtest_server_id = "{{system_service_speedtest_server_id}}"
