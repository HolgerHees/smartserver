<?php
require "../shared/libs/logfile.php";
require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/ressources.php";

require "inc/job.php";
require "inc/job_template.php";
require "config.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link rel="stylesheet" href="/shared/css/logfile/logfile_box.css">
<link rel="stylesheet" href="./css/core.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="/shared/js/logfile/logfile.js"></script>
<script src="./js/core.js"></script>
<script src="./js/list.js"></script>
<script>
function initPage()
{
    mx.CIList.init(mx.$$('div.row'),mx.$("div.table"), 'div.state', 'span.state','span.runtime');
    mx.CIList.startUpdateProcess();
    mx.Page.refreshUI();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer-800", "CI Service"); } );</script>
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
