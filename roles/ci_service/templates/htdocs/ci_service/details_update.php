<?php
require "../shared/libs/logfile.php";

require "inc/job.php";
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
    $logfile = new LogFile($log_folder,basename($matches[0]));
    $logfile->init($position);

    $job = new Job(basename($matches[0]));
?>
<div id="currentPosition"><?php echo $logfile->getBytes(); ?></div>
<div id="state"><?php echo $job->getState(); ?></div>
<div id="stateFormatted"><?php echo LogFile::formatState($job->getState()); ?></div>
<div id="duration"><?php echo $job->getDuration(); ?></div>
<div id="durationFormatted"><?php echo LogFile::formatDuration($job->getDuration()); ?></div>
<div id="logs"><?php
    foreach( $logfile->getLines() as $line )
    {
        echo LogFile::getLogLine($line);
    }
}
?></div>
