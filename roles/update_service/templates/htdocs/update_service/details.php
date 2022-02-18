<?php
require "../shared/libs/logfile.php";
require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "inc/job_template.php";
require "inc/job.php";

require "config.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

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
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
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
       
    mx.Page.init();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body class="inline">
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
</script>
<?php
    echo '<div class ="header form table logfileBox">' . JobTemplate::getDetails($job,false) . '</div><div class="scrollControl" onClick="mx.Logfile.toggleBottomScroll()"></div><div class="goToControl"><div></div></div>';

    echo '<div class="log">';
    
    foreach( $logfile->getLines() as $line )
    {
        echo LogFile::getLogLine($line);
    }
    
    echo '</div>';
?>
</body>
</html>
