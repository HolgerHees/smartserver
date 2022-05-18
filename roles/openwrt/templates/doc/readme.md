# 1. Preparations

    Set root password and switch lan interface to dhcp
    
    Set hostname & timezone

# 2. Firewall

    Setup public firewall zone

![firewall_settings](./img/firewall_settings.png) ![firewall_overview](./img/firewall_overview.png)

# 3. Network & DHCP Server

    Setup vlan together with lan and public interface

![network_device](./img/network_device.png) ![network_interface_lan](./img/network_interface_lan.png) ![network_interface_public](./img/network_interface_public.png)

    Make also sure that dhcp server is disabled on all interfaces

![network_dhcp](./img/network_dhcp.png)

# 4. Backup

    /etc/shadow => /smartserver/config/{config}/vault/openwrt/{ip}/etc/shadow
    /etc/config/system => /smartserver/config/{config}/vault/openwrt/{ip}/etc/config/system
    /etc/config/firewall => /smartserver/config/{config}/vault/openwrt/{ip}/etc/config/firewall
    /etc/config/network => /smartserver/config/{config}/vault/openwrt/{ip}/etc/network
    /etc/config/dhcp => /smartserver/config/{config}/vault/openwrt/{ip}/etc/network

# 5. Run ansible

    ansible-playbook -i config/{config}}/server_local.ini --ask-vault-pass --tags="openwrt" server.yml
