<?php
/* Servers configuration */
$i = 0;

/* Server: openhab [1] */
$i++;
//$cfg['Servers'][$i]['verbose'] = 'openhab';
$cfg['Servers'][$i]['host'] = 'mariadb';
$cfg['Servers'][$i]['port'] = '';
$cfg['Servers'][$i]['socket'] = '';
$cfg['Servers'][$i]['connect_type'] = 'tcp';
#$cfg['Servers'][$i]['nopassword'] = true;
$cfg['Servers'][$i]['AllowNoPassword'] = true;
$cfg['Servers'][$i]['auth_type'] = 'config';
$cfg['Servers'][$i]['user'] = 'root';
//$cfg['Servers'][$i]['password'] = '';

/* End of servers configuration */

$cfg['AllowThirdPartyFraming'] = true;
$cfg['NavigationDisplayLogo'] = false;
$cfg['NavigationDisplayServers'] = false;
$cfg['DefaultLang'] = 'en';
$cfg['ServerDefault'] = 1;
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';
?>
