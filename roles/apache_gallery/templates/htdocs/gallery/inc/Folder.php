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
            $date = new DateTime();
            $date->setTimestamp($data[4]);

            $images[] = new Image($this->sub_folder, $data[2], $data[1], $data[0], $date );
        }

        usort($images,function($a,$b){
            $aTimestamp = $a->getTime()->getTimestamp();
            $bTimestamp = $b->getTime()->getTimestamp();

            if( $aTimestamp < $bTimestamp ) return 1; 
            if( $aTimestamp > $bTimestamp ) return -1;
            
            return strcmp($a->getOriginalCacheName(), $b->getOriginalCacheName()) * -1;
        });

        return $images;
    }
}
