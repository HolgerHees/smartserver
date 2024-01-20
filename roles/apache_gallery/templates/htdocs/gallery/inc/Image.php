<?php
class Image {
    private $name = null;
    private $original_cache_name = null;
    private $datetime = null;
    private $slot = null;
    
    public function __construct($name, $org_cache_name, $timestamp ) {
        $this->name = $name;
        $this->original_cache_name = $org_cache_name;

        $datetime = new DateTime();
        $datetime->setTimestamp($timestamp);
        $this->datetime = $datetime;

        $date = clone $this->datetime;
        $date->setTime( $date->format("H"), 0, 0, 0 );
        $date->add(new DateInterval('PT1H'));
        $this->slot = $date->getTimestamp();
    }
    
    public function getName()
    {
        return $this->name;
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
