<?php
require "inc/job.php";
require "inc/job_template.php";
require "config.php";

$datetime = isset($_GET['datetime']) ? $_GET['datetime'] : "";
$config = isset($_GET['config']) ? $_GET['config'] : "";
$os = isset($_GET['os']) ? $_GET['os'] : "";
$branch = isset($_GET['branch']) ? $_GET['branch'] : "";
$hash = isset($_GET['hash']) ? $_GET['hash'] : "";

$matches = glob($log_folder . $datetime . '-*-' . $config . '-' . $os . '-' . $branch . '-' . $hash . '*.log' );

if( sizeof($matches) == 1 )
{
    $job = new Job($log_folder,basename($matches[0]));
    $job->initContent(0);
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
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
<link rel="stylesheet" href="./css/core.css">
<link rel="stylesheet" href="./css/details.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
<script src="js/core.js"></script>
<script src="js/details.js"></script>
<script>
function initPage()
{
    var body = mx.$('body');
    var goToControl = document.querySelector('div.goToControl');
    mx.CIDetails.init(<?php echo $job->getDuration(); ?>,mx.$("div.state"),mx.$("span.state"),mx.$('span.runtime'), mx.$('div.log'));
    
<?php if( $job->getState() == 'running' ){ ?>
    mx.CIDetails.startUpdateProcess(<?php echo $job->getBytes(); ?>);
<?php } else { ?>
    var scrollControl = document.querySelector('div.scrollControl');
    scrollControl.style.display = "none";
    goToControl.classList.add("singleButton");
<?php } ?>

    mx.$('div.log').addEventListener("scroll", function(e) { 
        mx.CIDetails.checkScrollPosition(e,body,goToControl,true);
    },false);

    window.addEventListener("scroll",function(e)
    {
        mx.CIDetails.checkScrollPosition(e,body,goToControl,false);
    });
    mx.CIDetails.checkScrollPosition(null,body,goToControl,false);
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
</script>
<?php
    echo '<div class ="header form table">' . JobTemplate::getDetails($job,false) . '</div><div class="scrollControl" onClick="mx.CIDetails.toggleBottomScroll()"></div><div class="goToControl"><div></div></div><div class="log">';
    
    foreach( $job->getLines() as $line )
    {
        echo JobTemplate::getLogLine($line);
    }
    
    echo '</div>';
?>
</body>
</html>
