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
        $file_times = array();
        $list = shell_exec("stat -c \"%y %n\" " . $this->main_folder . $this->sub_folder . "/* 2>/dev/null");
        foreach( explode("\n",$list) as $line )
        {
            if( empty($line) ) continue;
            
            $parts = explode(" ",$line);
            
            $time = strtotime($parts[0] . " " . $parts[1] . " " . $parts[2]);
            $time = DateTime::createFromFormat('Y-m-d H:i:s O', $parts[0] . " " . explode(".",$parts[1])[0] . " " . $parts[2]);
            $file_times[$parts[3]] = $time;
        }
        
        $images = [];
        $files = scandir($this->main_folder . $this->sub_folder);
        foreach( $files as $file )
        {
            if( $file == '.' or $file == '..' || is_dir($this->sub_folder.$file) ) continue;
            $images[] = new Image($this->main_folder , $this->sub_folder, $file, $file_times[ $this->main_folder . $this->sub_folder . "/" . $file ] );
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
