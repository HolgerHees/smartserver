<?php
require "../shared/libs/logfile.php";
require "inc/job.php";
require "inc/job_template.php";
require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

$entityBody = file_get_contents('php://input');

$data = json_decode($entityBody);
if( !$data )
{
    echo 'not able to parse json';
    exit(1);
}

$jobs = Job::getJobs($log_folder);

$new_jobs = "";
$running_jobs = "";
$removed_jobs = [];

$available_jobs = array();

foreach( $jobs as $job )
{
    $available_jobs[] = $job->getHash();
    
    if( !in_array($job->getHash(),$data->visibleJobs) )
    {
        $new_jobs .= JobTemplate::getDetails($job,true);
    }
    elseif( in_array($job->getHash(),$data->runningJobs) )
    {
        $running_jobs .= '<div id="' . $job->getHash() . '">';
        $running_jobs .= '    <div class="state">' . $job->getState() . '</div>';
        $running_jobs .= '    <div class="stateFormatted">' . LogFile::formatState($job->getState()) . '</div>';
        $running_jobs .= '    <div class="duration">' . $job->getDuration() . '</div>';
        $running_jobs .= '    <div class="durationFormatted">' . Logfile::formatDuration($job->getDuration()) . '</div>';
        $running_jobs .= '</div>';
    }
}

foreach( $data->visibleJobs as $visible_job_hash )
{
    if( !in_array($visible_job_hash,$available_jobs) )
    {
        $removed_jobs[] = $visible_job_hash;
    }
}

echo '<div id="newJobs">' . $new_jobs . '</div>';
echo '<div id="runningJobs">' . $running_jobs . '</div>';
echo '<div id="removedJobs">' . join(",",$removed_jobs) . '</div>';
