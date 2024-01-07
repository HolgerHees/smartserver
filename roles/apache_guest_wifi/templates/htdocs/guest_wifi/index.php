<?php
include 'config.php';
include 'qrcode.php';

if( empty($_GET['name']) )
{
    echo "missing name";
    exit(0);
}

$options = [ 'w' => 350, 'h' => 350, 'wq' => 1 ];

if( $_GET['obfuscated'] == "-1" )
{
    $name = "honeypot";
    $password = "honeypot";
    $data = "WIFI:T:WPA;S:" . $name . ";P:" . $password . ";;";
    #$options["bc"] = "#FF0000";
}
elseif( $_GET['obfuscated'] == "0" )
{
    $name = $_GET['name'];
    $password = $wifi_networks[$name];
    $data = "WIFI:T:WPA;S:" . $name . ";P:" . $password . ";;";
}
else
{
    $data = "honeypot";
}

$generator = new QRCode($data, $options);
/* Output directly to standard output. */
$generator->output_image();
