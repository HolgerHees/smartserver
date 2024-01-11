<?php
class Folder {
    private $main_folder = null;
    private $sub_folder = null;
    
    public function __construct($main_folder , $sub_folder ) {
        $this->main_folder = $main_folder;
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
        foreach( $files as $file )
        {
            if( $file == '.' or $file == '..' || is_dir($this->sub_folder.$file) ) continue;

            $path = $this->main_folder . $this->sub_folder . "/" . $file;

            $timestamp = filemtime($path);
            $date = new DateTime();
            $date->setTimestamp($timestamp);

            $images[] = new Image($this->main_folder , $this->sub_folder, $file, $date );
        }

        usort($images,function($a,$b){
            $aTimestamp = $a->getTime()->getTimestamp();
            $bTimestamp = $b->getTime()->getTimestamp();

            if( $aTimestamp < $bTimestamp ) return 1; 
            if( $aTimestamp > $bTimestamp ) return -1;
            
            return strcmp($a->getFile(), $b->getFile()) * -1;
        });
        
        return $images;
    }
}
