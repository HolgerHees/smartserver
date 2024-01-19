<?php
class Image {
    private $main_folder = null;
    private $sub_folder = null;
    private $file = null;
    private $time = null;
    
    public function __construct($sub_folder, $small_cache_name, $medium_cache_name, $org_cache_name, $creation_time ) {
        $this->sub_folder = $sub_folder;
        $this->small_cache_name = $small_cache_name;
        $this->medium_cache_name = $medium_cache_name;
        $this->original_cache_name = $org_cache_name;
        $this->time = $creation_time;
    }
    
    public function getSubFolder()
    {
        return $this->sub_folder;
    }

    public function getSmallCacheName()
    {
        return $this->small_cache_name;
    }

    public function getMediumCacheName()
    {
        return $this->medium_cache_name;
    }

    public function getOriginalCacheName()
    {
        return $this->original_cache_name;
    }

    public function getTime()
    {
        return $this->time;
    }
}
