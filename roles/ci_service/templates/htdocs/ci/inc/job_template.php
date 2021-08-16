<?php
class JobTemplate
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
              if( isset(JobTemplate::$map[$match[1]]) )
              {
                  return JobTemplate::$map[$match[1]];
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

    public static function getState($job)
    {
        $result = '<span class="state ' . $job->getState() . ' icon-resize-horizontal"><span class="text">' . $job->getState() . '</span>';
        switch( $job->getState() )
        {
            case 'running':
                $result .= '<span class="icon-dot"></span>';
                break;
            case 'success':
                $result .= '<span class="icon-ok"></span>';
                break;
            case 'failed':
                $result .= '<span class="icon-cancel"></span>';
                break;
            case 'retry':
                $result .= '<span class="icon-ccw"></span>';
                break;
            case 'stopped':
                $result .= '<span class="icon-block"></span>';
                break;
        }
        $result .= '</span>';
        return $result;
    }
    
    public static function getDetails($job,$list_view)
    {
        $result = '<div id="' . $job->getHash() . '" data-state="' . $job->getState() . '" data-duration="' . $job->getDuration() . '" class="row"';
        if( $list_view ) 
        {
          $result .= ' onClick="mx.CICore.openDetails(event,\''.$job->getDateTimeRaw().'\',\''.$job->getConfig().'\',\''.$job->getOs().'\',\''.$job->getBranch().'\',\''.$job->getGitHash().'\')"';
        }
        else
        {
          $result .= ' onClick="mx.CICore.openOverview(event)"';
        }
        $result .= '>';
        $result .= '<div class="state ' . $job->getState() . '"></div>';
        $result .= '<div><span class="icon-down branch">' . $job->getBranch() . '</span><span class="author">' . $job->getAuthor(). '<span></div>';
        $result .= '<div class="subject"><div>' . $job->getSubject() . '</div></div>';
        
        $result .= '<div>' . $job->getConfig() . '</div>';
        $result .= '<div>' . $job->getOs() . '</div>';

        $result .= '<div>' . JobTemplate::getState($job) . '<span class="hash icon-resize-horizontal" onClick="mx.CICore.openGitCommit(event,\'https://github.com/HolgerHees/smartserver/commit/'.$job->getGitHash().'\');"><span>' . substr($job->getGitHash(),0,7) . '</span><span class="icon-export"></span></span></div>';
        
        $result .= '<div><span class="runtime icon-clock">' . JobTemplate::formatDuration($job->getDuration()) . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>';
        $result .= '</div>';
        
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
?>
