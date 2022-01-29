<?php 
class LogFile
{
    private static $map = array(
      '0' => "</span>",
      '1' => "<span style='font-weight:bold'>",
      '0;31' => "<span style='color:#cc0000'>", // red
      '0;32' => "<span style='color:green'>",
      '0;33' => "<span style='color:#b2580c'>", // darkyellow
      '0;35' => "<span style='color:magenta'>",
      '0;36' => "<span style='color:cyan'>",
      '1;30' => "<span style='color:gray'>",
      '1;31' => "<span style='color:red'>",     // lightred 
      '1;32' => "<span style='color:#00cc00'>", // lightgreen
      '1;33' => "<span style='color:yellow'>",
      '1;35' => "<span style='color:plum'>"
    );
   
    public function __construct($log_path,$filename) 
    {
        $this->path = $log_path.$filename;
    }
    
    public function init($position)
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

    public static function getLogLine($line)
    {
        $result = '<div>';

        // format datetime
        if( preg_match("/^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}.*$/", $line) )
        {
            $result .= '<span style="color:#5a595c">' . substr($line,0,12) . '</span>';
            $line = substr($line,12);
        }
        
        // force whitespaces
        $line = preg_replace('/\s\s+/',"<span style='white-space: pre;'>$0</span>",$line);
        
        // convert color codes
        $line = preg_replace_callback(
          '|\x1b\[([;0-9]+?)m|',
          function ($match) {
              if( isset(LogFile::$map[$match[1]]) )
              {
                  return LogFile::$map[$match[1]];
              }
              else
              {
                  error_log("color code '" . $match[1] . "' not found.");
                  return $match[0];
              }
          },
          $line
        );
  
        // print final line
        $result .= $line;

        $result .= "</div>";
        
        return $result;
    }

    public static function formatDuration($duration) 
    {
      $days = floor($duration / 86400);
      $duration -= $days * 86400;
      $hours = floor($duration / 3600);
      $duration -= $hours * 3600;
      $minutes = floor($duration / 60);
      $seconds = $duration - $minutes * 60;
      
      if( $hours < 10 ) $hours = '0'.$hours;
      if( $minutes < 10 ) $minutes = '0'.$minutes;
      if( $seconds < 10 ) $seconds = '0'.$seconds;

      return $hours.':'.$minutes.':'.$seconds;
    }
}
