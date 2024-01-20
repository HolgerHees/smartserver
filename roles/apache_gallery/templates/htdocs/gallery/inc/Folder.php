<?php
include "Preview.php";

class Folder {
    private $sub_folder = null;

    public function __construct($sub_folder) {
        $this->sub_folder = $sub_folder;
    }
    
    public function getImageCount()
    {
        return Preview::getCount($this->sub_folder);
    }
    
    
    public function getImages()
    {
        $files = Preview::getFiles($this->sub_folder);

        $images = [];
        foreach( $files as $data )
        {
            $images[] = new Image($this->sub_folder, $data["small"], $data["medium"], $data["original"], $data["timestamp"] );
        }

        usort($images,function($a,$b){
            $aTimestamp = $a->getDateTime()->getTimestamp();
            $bTimestamp = $b->getDateTime()->getTimestamp();

            if( $aTimestamp < $bTimestamp ) return 1; 
            if( $aTimestamp > $bTimestamp ) return -1;
            
            return strcmp($a->getOriginalCacheName(), $b->getOriginalCacheName()) * -1;
        });

        return $images;
    }
}
