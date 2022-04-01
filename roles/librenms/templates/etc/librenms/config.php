<?php

$config['snmp']['community'] = array('public');

$config['nets'][] = "192.168.0.0/24";


$config['discovery_modules']['discovery-arp'] = true;

$config['discovery_modules']['ports-stack'] = false;
$config['discovery_modules']['cisco-vrf-lite'] = false;
