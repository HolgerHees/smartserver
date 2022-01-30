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

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
<link rel="stylesheet" href="/shared/css/logfile_box.css">
<link rel="stylesheet" href="./css/core.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
<script src="/shared/js/logfile.js"></script>
<script src="js/core.js"></script>
<script src="js/list.js"></script>
<script>
function initPage()
{
    mx.CIList.init(mx.$$('div.row'),mx.$("div.table"), 'div.state', 'span.state','span.runtime');
    mx.CIList.startUpdateProcess();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body class="inline">
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
</script>
<div class="form table logfileBox">
<?php
$jobs = Job::getJobs($log_folder);
foreach( $jobs as $job )
{
    echo JobTemplate::getDetails($job,true);
}
?>
</div>
</body>
</html>
