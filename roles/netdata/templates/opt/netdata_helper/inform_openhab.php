<?php
include "{{projects_path}}toolbox/_lib/init.php";

$rest = Setup::getOpenHabRest();

$content = Request::makeRequest("http://localhost:19999/api/v1/alarms?active&_=" . time(),[],null,200);

if($content)
{
    $data = json_decode($content);
    $alarms = (array)$data->{'alarms'};
    
    $level = 0;
    foreach( $alarms as $alarm )
    {
        switch( $alarm->{'status'} )
        {
            case "WARNING":
                if( $level < 1 ) $level = 1;
                break;
            case "CRITICAL":
                if( $level < 2 ) $level = 2;
                break;
        }
    }
    
    $rest->updateItem("State_Server",$level);
}
else
{
    exit("Netdata is down. Can't inform openhab about system status.");
}
