check for wpa3
https://forum.openwrt.org/t/wpa3-can-i-see-which-encryption-each-client-is-using/51798/7

hostapd_cli -i wlan1 all_sta | grep AKMSuiteSelector


