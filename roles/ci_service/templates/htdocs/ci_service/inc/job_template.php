<?php
class JobTemplate
{
    public static function getDetails($job,$list_view)
    {
        $result = '<div id="' . $job->getHash() . '" data-state="' . $job->getState() . '" data-duration="' . $job->getDuration() . '" class="row"';
        if( $list_view ) 
        {
          $result .= ' onClick="mx.CICore.openDetails(event,\''.$job->getConfig().'\',\''.$job->getOs().'\',\''.$job->getBranch().'\',\''.$job->getGitHash().'\')"';
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

        $result .= '<div>' . LogFile::formatState($job->getState()) . '<span class="hash icon-resize-horizontal" onClick="mx.CICore.openGitCommit(event,\'https://github.com/HolgerHees/smartserver/commit/'.$job->getGitHash().'\');"><span>' . substr($job->getGitHash(),0,7) . '</span><span class="icon-export"></span></span></div>';
        
        $result .= '<div><span class="runtime icon-clock">' . LogFile::formatDuration($job->getDuration()) . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>';
        $result .= '</div>';
        
        return $result;
    }    
}
?>
