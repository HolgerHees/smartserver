<?php
class Job {
    private $datetime = null;
    private $datetime_raw = null;
    private $duration = 0;
    private $state = "";
    private $config = "";
    private $os = "";
    private $branch = "";
    private $git_hash = "";
    private $author = "";
    private $subject = "";
    private $bytes = 0;
    private $content = [];
    
    public function __construct($filename) {
        $data = explode("-",$filename);

        #2020.01.29_14.30.00-3378-success-demo-suse-a3e8e2c556f54dfaba5f880f9f91bdb6aebad55d.log
        $this->datetime = DateTime::createFromFormat("Y.m.d_H.i.s",$data[0],new DateTimeZone('Europe/Berlin'));
        $this->datetime_raw = $data[0];
               
        $this->state = $data[2];
        $this->cmd = $data[3];
        $this->username = explode(".",$data[4])[0];

        $this->duration = $data[1];
        if( $this->duration == 0 && $this->state == "running" ) 
        {
            $now = new DateTime("now",new DateTimeZone('Europe/Berlin'));
            $this->duration = $now->getTimestamp() - $this->datetime->getTimestamp();
        }
    }
    
    public static function getJobs($log_folder)
    {
        $files = scandir($log_folder);
        $jobs = [];
        foreach( $files as $file )
        {
            if( $file == '.' or $file == '..' || is_dir($log_folder.$file) )
            {
                continue;
            }
            
            $job = new Job($file);
            
            $jobs[] = $job;
        }

        usort( $jobs, function( $job1, $job2 )
        {
            if( $job1->getDateTime()->getTimestamp() > $job2->getDateTime()->getTimestamp() ) return -1;
            if( $job1->getDateTime()->getTimestamp() < $job2->getDateTime()->getTimestamp() ) return 1;
            return 0;
        });
        return $jobs;
    }
       
    public function getHash()
    {
        return md5($this->datetime_raw.':'.$this->username.':'.$this->cmd);
    }
        
    public function getDateTime()
    {
        return $this->datetime;
    }
    
    public function getDateTimeRaw()
    {
        return $this->datetime_raw;
    }

    public function getDuration()
    {
        return $this->duration;
    }
    
    public function getState()
    {
        return $this->state;
    }

    public function getUsername()
    {
        return $this->username;
    }

    public function getCmd()
    {
        return $this->cmd;
    }
}
