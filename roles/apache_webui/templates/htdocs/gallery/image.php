<?php
include "config.php";

if( empty($_GET["sub"]) || empty($_GET["image"]) )
{
    exit;
}

header('Content-Type: image/jpeg');

echo file_get_contents( $ftp_folder . $_GET["sub"] . "/" . $_GET["image"] );
