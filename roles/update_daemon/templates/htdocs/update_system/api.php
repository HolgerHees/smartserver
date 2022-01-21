<?php
require "config.php";

$name = $_SERVER['REMOTE_USERNAME'];
$groups = [];
$handle = fopen("../secret/.htdata", "r");
if ($handle) {
    while (($line = fgets($handle)) !== false) {
        list($_username,$_name,$_groups) = explode(":", $line);
        if( trim($_username) == $name )
        {
            $name = trim($_name);
            $groups = explode(",",trim($_groups));
            break;
        }
    }

    fclose($handle);
}

if( !in_array("admin",$groups) )
{
    header('HTTP/1.0 403 Forbidden');
    echo 'You are forbidden!';
    exit;
}

$entityBody = file_get_contents('php://input');
$data = json_decode($entityBody);

if( !$data || empty($data->action) )
{
    header('HTTP/1.0 404 Not Found');
    echo 'Action not found';
    exit;
}

$action = $data->action;

$post = [];
if( !empty($data->parameter) )
{
    $post['parameter'] = $data->parameter;
}

$ch = curl_init("http://".$daemon_ip.":8505/" . $action . '/' ); // such as http://example.com/example.xml
curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, 0);
$data = curl_exec($ch);
curl_close($ch);

echo $data;
#error_log($action . ( $parameter ? " " . $parameter : "" ));
