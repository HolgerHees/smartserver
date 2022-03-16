<?php
require "../shared/libs/logfile.php";
require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/i18n.php";

require "inc/job.php";

require "config.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

$position = isset($_GET['position']) ? $_GET['position'] : 0;

$datetime = isset($_GET['datetime']) ? $_GET['datetime'] : "";
$cmd = isset($_GET['cmd']) ? $_GET['cmd'] : "";
$username = isset($_GET['username']) ? $_GET['username'] : "";

$matches = glob($deployment_logs_folder . $datetime . '-*-' . $cmd . '-' . $username . '.log' );

if( sizeof($matches) == 1 )
{
    $logfile = new LogFile($deployment_logs_folder,basename($matches[0]));
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
