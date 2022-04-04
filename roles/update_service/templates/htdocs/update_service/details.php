<?php
require "../shared/libs/logfile.php";
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "inc/job.php";

require "config.php";

$datetime = isset($_GET['datetime']) ? $_GET['datetime'] : "";
$cmd = isset($_GET['cmd']) ? $_GET['cmd'] : "";
$username = isset($_GET['username']) ? $_GET['username'] : "";

$matches = glob($deployment_logs_folder . $datetime . '-*-' . $cmd . '-' . $username . '.log' );

if( sizeof($matches) == 1 )
{
    $logfile = new LogFile($deployment_logs_folder,basename($matches[0]));
    $logfile->init(0);
    
    $job = new Job(basename($matches[0]));
}
else if( sizeof($matches) > 1 )
{
    echo 'too many files found';
    print_r($matches);
    exit();
}
else
{
    echo 'no file found';
    exit();
}

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link rel="stylesheet" href="/shared/css/logfile/logfile.css">
<link rel="stylesheet" href="/shared/css/logfile/logfile_box.css">
<link rel="stylesheet" href="../css/core.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="/shared/js/logfile/logfile.js"></script>
<script>
mx.CICore = (function( ret ) {
    ret.openOverview = function(event)
    {
        document.location = '../system/';
    }
    return ret;
})( mx.CICore || {} );

function initPage()
{
    var body = mx.$('body');
    var goToControl = document.querySelector('div.goToControl');
    mx.Logfile.init(<?php echo $job->getDuration(); ?>,mx.$("div.state"),mx.$("span.state"),mx.$('span.runtime'), mx.$('div.log'), mx.Host.getBase() + '../details_update/' );
    
<?php if( $job->getState() == 'running' ){ ?>
    mx.Logfile.startUpdateProcess(<?php echo $logfile->getBytes(); ?>);
<?php } else { ?>
    var scrollControl = document.querySelector('div.scrollControl');
    scrollControl.style.display = "none";
    goToControl.classList.add("singleButton");
<?php } ?>

    mx.$('div.log').addEventListener("scroll", function(e) { 
        mx.Logfile.checkScrollPosition(e,body,goToControl,true);
    },false);

    window.addEventListener("scroll",function(e)
    {
        mx.Logfile.checkScrollPosition(e,body,goToControl,false);
    });
    mx.Logfile.checkScrollPosition(null,body,goToControl,false);
       
    mx.Page.refreshUI();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, mx.I18N.get("Job details - <?php echo $cmd; ?>")); } );</script>
<?php
    echo '<div class ="header form table logfileBox">
    
    <div id="' . $job->getHash() . '" data-state="' . $job->getState() . '" data-duration="' . $job->getDuration() . '" class="row" onClick="mx.CICore.openOverview(event)">
    <div class="state ' . $job->getState() . '"></div>
    
    <div class="cmd" >' . $job->getCmd() . '</div>
    <div class="username" >' . $job->getUsername() . '</div>

    <div>' . LogFile::formatState($job->getState()) . '</div>
    
    <div><span class="runtime icon-clock">' . explode(".",LogFile::formatDuration($job->getDuration()))[0] . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>
    </div>

    </div><div class="scrollControl" onClick="mx.Logfile.toggleBottomScroll()"></div><div class="goToControl"><div></div></div>';

    echo '<div class="log">';
    
    foreach( $logfile->getLines() as $line )
    {
        echo LogFile::getLogLine($line);
    }
    
    echo '</div>';
?>
</body>
</html>
