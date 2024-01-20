<?php
class Image {
    private $sub_folder = null;
    private $small_cache_name = null;
    private $medium_cache_name = null;
    private $original_cache_name = null;
    private $datetime = null;
    private $slot = null;
    
    public function __construct($sub_folder, $small_cache_name, $medium_cache_name, $org_cache_name, $timestamp ) {
        $this->sub_folder = $sub_folder;
        $this->small_cache_name = $small_cache_name;
        $this->medium_cache_name = $medium_cache_name;
        $this->original_cache_name = $org_cache_name;

        $datetime = new DateTime();
        $datetime->setTimestamp($timestamp);
        $this->datetime = $datetime;

        $date = clone $this->datetime;
        $date->setTime( $date->format("H"), 0, 0, 0 );
        $date->add(new DateInterval('PT1H'));
        $this->slot = $date->getTimestamp();
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

    public function getDateTime()
    {
        return $this->datetime;
    }

    public function getSlot()
    {
        return $this->slot;
    }
}
