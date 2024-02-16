<?php
require "./libs/ressources.php";
require "./libs/http.php";

if( empty($_GET['type']) || empty($_GET['path']) ) 
{
  HttpResponse::throwNotFound();
}

$type = $_GET['type'];
$path = $_GET['path'];
$version = empty($_GET['version']) ? -1 : $_GET['version'];

$dir = __DIR__ . "/.." . $path; 
$dir = realpath($dir) . "/";

if( !str_starts_with( $dir,  realpath(__DIR__ . "../../" ) ) )
{
  HttpResponse::throwForbidden();
}

list($type, $content) = Ressources::build($type, $dir, $path);

header("Content-Type: " . $type);
echo $content;

