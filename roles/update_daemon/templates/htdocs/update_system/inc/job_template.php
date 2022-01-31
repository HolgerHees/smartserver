<?php
class JobTemplate
{
    public static function getDetails($job,$list_view)
    {
        $result = '<div id="' . $job->getHash() . '" data-state="' . $job->getState() . '" data-duration="' . $job->getDuration() . '" class="row"';
        $result .= ' onClick="mx.CICore.openOverview(event)"';
        $result .= '>';
        $result .= '<div class="state ' . $job->getState() . '"></div>';

        $result .= '<div class="cmd" >' . $job->getCmd() . '</div>';
        $result .= '<div class="username" >' . $job->getUsername() . '</div>';

        $result .= '<div>' . LogFile::formatState($job->getState()) . '</div>';
        
        $result .= '<div><span class="runtime icon-clock">' . explode(".",LogFile::formatDuration($job->getDuration()))[0] . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>';
        $result .= '</div>';
        
        return $result;
    }    
}
?>
