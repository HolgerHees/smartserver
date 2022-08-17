<?php
include 'config.php';
include 'qrcode.php';

if( empty($_GET['name']) )
{
    echo "missing name";
    exit(0);
}

$name = $_GET['name'];
$password = $wifi_networks[$name];

$generator = new QRCode("WIFI:T:WPA;S:" . $name . ";P:" . $password . ";;", [ 'w' => 350, 'h' => 350, 'wq' => 1 ]);

/* Output directly to standard output. */
$generator->output_image();
