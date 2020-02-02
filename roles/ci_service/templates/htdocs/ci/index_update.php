<?php
require "inc/job.php";
require "inc/job_template.php";
require "config.php";

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

foreach( $jobs as $job )
{
    if( !in_array($job->getHash(),$data->visibleJobs) )
    {
        $new_jobs .= JobTemplate::getDetails($job,true);
    }
    elseif( in_array($job->getHash(),$data->runningJobs) )
    {
        $running_jobs .= '<div id="' . $job->getHash() . '">';
        $running_jobs .= '    <div class="state">' . $job->getState() . '</div>';
        $running_jobs .= '    <div class="stateFormatted">' . JobTemplate::getState($job) . '</div>';
        $running_jobs .= '    <div class="duration">' . $job->getDuration() . '</div>';
        $running_jobs .= '    <div class="durationFormatted">' . JobTemplate::formatDuration($job->getDuration()) . '</div>';
        $running_jobs .= '</div>';
    }
}

echo '<div id="newJobs">' . $new_jobs . '</div>';
echo '<div id="runningJobs">' . $running_jobs . '</div>';
