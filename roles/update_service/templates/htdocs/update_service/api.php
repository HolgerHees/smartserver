<?php
require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

$entityBody = file_get_contents('php://input');
$data = json_decode($entityBody, true);

if( !$data || empty($data["action"]) )
{
    HttpResponse::throwNotFound();
}

$action = $data["action"];

$post = empty($data["parameter"]) ? [] : $data["parameter"];

$post['username'] = Auth::getUser();

$ch = curl_init("http://".$service_ip.":8505/" . $action . '/' ); // such as http://example.com/example.xml
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($post));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, 0);
$data = curl_exec($ch);

$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
if( $code == 0 ) $code = 503;

header('HTTP/1.0 ' . $code . " " . HttpResponse::getStatusReason($code));
curl_close($ch);

echo $data;
#error_log($action . ( $parameter ? " " . $parameter : "" ));
