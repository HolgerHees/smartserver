<?php
include "Preview.php";

class Folder {
    private $main_folder = null;
    private $sub_folder = null;
    
    public function __construct($sub_folder) {
        $this->main_folder = FTP_FOLDER;
        $this->sub_folder = $sub_folder;
    }
    
    public function getImageCount()
    {
        return intval( shell_exec("ls -1 " . $this->main_folder . $this->sub_folder . "/* | wc -l") );
    }
    
    
    public function getImages()
    {
        $images = [];
        $files = scandir($this->main_folder . $this->sub_folder);
        foreach( $files as $filename )
        {
            if( $filename == '.' || $filename == '..' || is_dir($this->sub_folder.$filename) ) continue;

            $path = $this->main_folder . $this->sub_folder . "/" . $filename;

            $timestamp = filemtime($path);
            $date = new DateTime();
            $date->setTimestamp($timestamp);

            list( $small_cache_name, $medium_cache_name, $org_cache_name ) = Preview::check($path, false);

            if( $org_cache_name == null ) continue;

            $images[] = new Image($this->sub_folder, $small_cache_name, $medium_cache_name, $org_cache_name, $date );
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
