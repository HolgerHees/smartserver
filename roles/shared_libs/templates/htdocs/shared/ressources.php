<?php
require "./libs/ressources.php";
require "./libs/http.php";

if( empty($_GET['type']) || empty($_GET['path']) ) 
{
  HttpResponse::throwNotFound();
}

$path = $_GET['path'];

$dir = __DIR__ . "/.." . $path; 
$dir = realpath($dir) . "/";

if( !str_starts_with( $dir,  realpath(__DIR__ . "../../" ) ) )
{
  HttpResponse::throwForbidden();
}

        
Ressources::dump($_GET['type'], $dir, $path);
