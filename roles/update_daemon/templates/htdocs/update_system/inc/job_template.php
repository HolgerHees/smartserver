<?php
class JobTemplate
{
    public static function getState($job)
    {
        $result = '<span class="state ' . $job->getState() . '"><span class="text">' . $job->getState() . '</span>';
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
        $result .= ' onClick="mx.CICore.openOverview(event)"';
        $result .= '>';
        $result .= '<div class="state ' . $job->getState() . '"></div>';

        $result .= '<div class="cmd" >' . $job->getCmd() . '</div>';
        $result .= '<div class="username" >' . $job->getUsername() . '</div>';

        $result .= '<div>' . JobTemplate::getState($job) . '</div>';
        
        $result .= '<div><span class="runtime icon-clock">' . explode(".",LogFile::formatDuration($job->getDuration()))[0] . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>';
        $result .= '</div>';
        
        return $result;
    }    
}
?>
