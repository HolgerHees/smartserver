<?php
require "inc/job.php";
require "inc/job_template.php";
require "config.php";

$position = isset($_GET['position']) ? $_GET['position'] : 0;

$datetime = isset($_GET['datetime']) ? $_GET['datetime'] : "";
$config = isset($_GET['config']) ? $_GET['config'] : "";
$os = isset($_GET['os']) ? $_GET['os'] : "";
$branch = isset($_GET['branch']) ? $_GET['branch'] : "";
$hash = isset($_GET['hash']) ? $_GET['hash'] : "";

$matches = glob($log_folder . $datetime . '-*-' . $config . '-' . $os . '-' . $branch . '-' . $hash . '*.log' );
if( sizeof($matches) == 1 )
{
    $job = new Job($log_folder,basename($matches[0]));
    $job->initContent($position);
?>
<div id="currentPosition"><?php echo $job->getBytes(); ?></div>
<div id="state"><?php echo $job->getState(); ?></div>
<div id="stateFormatted"><?php echo JobTemplate::getState($job); ?></div>
<div id="duration"><?php echo $job->getDuration(); ?></div>
<div id="durationFormatted"><?php echo JobTemplate::formatDuration($job->getDuration()); ?></div>
<div id="logs"><?php
    foreach( $job->getLines() as $line )
    {
        echo JobTemplate::getLogLine($line);
    }
}
?></div>
