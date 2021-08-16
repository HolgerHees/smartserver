<?php
class Job {
    private $path = "";
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
    
    public function __construct($log_path,$filename) {
        $this->path = $log_path.$filename;
        
        $data = explode("-",$filename);

        #2020.01.29_14.30.00-3378-success-demo-suse-a3e8e2c556f54dfaba5f880f9f91bdb6aebad55d.log
        $this->datetime = DateTime::createFromFormat("Y.m.d_H.i.s",$data[0],new DateTimeZone('Europe/Berlin'));
        $this->datetime_raw = $data[0];
        
        $this->duration = $data[1];
        if( $this->duration == 0 ) 
        {
            $now = new DateTime("now",new DateTimeZone('Europe/Berlin'));
            $this->duration = $now->getTimestamp() - $this->datetime->getTimestamp();
        }
        
        $this->state = $data[2];
        $this->config = $data[3];
        $this->os = $data[4];
        $this->branch = $data[5];
        $this->git_hash = $data[6];
        $this->author = $data[7];
        $this->author = str_replace("_"," ",$this->author);
        $this->subject = explode(".",$data[8])[0];
        if( substr($this->subject,-1) == '_' ) $this->subject = substr($this->subject,0,strlen($this->subject)-1) . '...';
        $this->subject = str_replace("_"," ",$this->subject);
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
            
            $job = new Job($log_folder,$file);
            
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
    
    public function initContent($position)
    {
        $this->bytes = $position;
        $this->content = [];
        $current_bytes = filesize($this->path);
        
        if($current_bytes > $this->bytes)
        {
            $data = file_get_contents($this->path, false, null, $this->bytes);
            $this->bytes += mb_strlen($data,"8bit");
            
            $this->content = explode("\n",$data);
        }
    }
    
    public function getHash()
    {
        return md5($this->datetime_raw.':'.$this->config.':'.$this->os.':'.$this->branch.':'.$this->git_hash);
    }
    
    public function getBytes()
    {
        return $this->bytes;
    }

    public function getLines()
    {
        return $this->content;
    }
    
    public function getPath()
    {
        return $this->path;
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

    public function getConfig()
    {
        return $this->config;
    }

    public function getOs()
    {
        return $this->os;
    }

    public function getBranch()
    {
        return $this->branch;
    }

    public function getGitHash()
    {
        return $this->git_hash;
    }

    public function getAuthor()
    {
        return $this->author;
    }

    public function getSubject()
    {
        return $this->subject;
    }
}
