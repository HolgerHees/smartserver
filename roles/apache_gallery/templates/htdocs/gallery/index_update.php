<?php

$entityBody = file_get_contents('php://input');

$data = json_decode($entityBody);
if( !$data )
{
    echo 'not able to parse json';
    exit(1);
}

include "inc/Image.php";
include "inc/Folder.php";
include "inc/Template.php";

include "config.php";

$folder = new Folder($data->sub);
$count = $folder->getImageCount();

if( $count != $data->count )
{
    $folder = new Folder($data->sub);
    $images = $folder->getImages();
    
    $starttime = Template::getStarttime($images);
    $endtime = Template::getEndtime($images);
    
    echo '<div id="slots">' . Template::getSlots($starttime,$endtime,$images) . '</div>';
    echo '<div id="gallery">' . Template::getImages($images) . '</div>';
}
