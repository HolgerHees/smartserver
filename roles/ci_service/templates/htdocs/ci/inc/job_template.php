<?php
class JobTemplate
{
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
        $result .= '<div><span class="icon-down branch">' . $job->getBranch() . '</span><span class="username">' . $job->getAuthor(). '<span></div>';
        $result .= '<div class="subject"><div>' . $job->getSubject() . '</div></div>';
        
        $result .= '<div>' . $job->getConfig() . '</div>';
        $result .= '<div>' . $job->getOs() . '</div>';

        $result .= '<div>' . JobTemplate::getState($job) . '<span class="hash icon-resize-horizontal" onClick="mx.CICore.openGitCommit(event,\'https://github.com/HolgerHees/smartserver/commit/'.$job->getGitHash().'\');"><span>' . substr($job->getGitHash(),0,7) . '</span><span class="icon-export"></span></span></div>';
        
        $result .= '<div><span class="runtime icon-clock">' . LogFile::formatDuration($job->getDuration()) . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>';
        $result .= '</div>';
        
        return $result;
    }    
}
?>
