<?php
require "../shared/libs/logfile.php";
require "inc/job.php";
require "inc/index_template.php";

require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

$entityBody = file_get_contents('php://input');
$forced_data = json_decode($entityBody, true);

$data = IndexTemplate::dump($system_state_file,$deployment_state_file,$deployment_tags_file,$deployment_logs_folder,$forced_data);

echo $data;
