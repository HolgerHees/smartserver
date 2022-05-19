# 1. Preparations

    Set root password and switch lan interface to dhcp
    
    Set hostname & timezone

# 2. Network

    Setup vlan together with lan and public interface

![network_device](./img/network_device.png) ![network_interface_lan](./img/network_interface_lan.png) ![network_interface_public](./img/network_interface_public.png)

    Make also sure that dhcp server is disabled on all interfaces

![network_dhcp](./img/network_dhcp.png)

# 3. Firewall & DHCP

    Setup public firewall zone, if needed. If you run your AP just as a dump AP you can disable firewall, dhcp and masquerading by addint the following snipped to /etc/rc.local
    
```
for i in firewall dnsmasq odhcpd; do
  if /etc/init.d/"$i" enabled; then
    /etc/init.d/"$i" disable
    /etc/init.d/"$i" stop
  fi
done
```

![firewall_settings](./img/firewall_settings.png) ![firewall_overview](./img/firewall_overview.png)

# 4. Backup

### 4.1 Common

    /etc/shadow => /smartserver/config/{config}/vault/openwrt/shared/etc/shadow
    /etc/config/network => /smartserver/config/{config}/vault/openwrt/shared/etc/config/network
    
    /etc/config/system => /smartserver/config/{config}/vault/openwrt/{ip}/etc/config/system

### 4.1 Firewall & DHCP specific

    /etc/config/rc.local => /smartserver/config/{config}/vault/openwrt/shared/etc/rc.local
    
    or

    /etc/config/dhcp => /smartserver/config/{config}/vault/openwrt/{ip}/etc/dhcp
    /etc/config/firewall => /smartserver/config/{config}/vault/openwrt/{ip}/etc/config/firewall
    
# 5. Run ansible

    ansible-playbook -i config/{config}}/server_local.ini --ask-vault-pass --tags="openwrt" server.yml
