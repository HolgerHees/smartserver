<?php
class Image {
    private $main_folder = null;
    private $sub_folder = null;
    private $file = null;
    private $time = null;
    
    public function __construct($main_folder , $sub_folder, $file, $creation_time ) {
        $this->main_folder = $main_folder;
        $this->sub_folder = $sub_folder;
        $this->file = $file;
        
        $this->time = $creation_time;
    }
    
    public function getFile()
    {
        return $this->file;
    }
    
    public function getPath()
    {
        return $this->main_folder . $this->sub_folder . "/" . $this->file;
    }
    
    public function getTime()
    {
        return $this->time;
    }
}
