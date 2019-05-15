<?php

$url = "http://localhost:19999/api/v1/alarms?active";
$ch = curl_init(); 
curl_setopt($ch, CURLOPT_URL, $url); 
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
$content = curl_exec($ch); 
curl_close($ch); 

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
    
    $url = "http://localhost:8080/rest/items/State_Server";

    $headers = array(
        'Accept: application/json',
        'Content-Type: text/plain',
    );

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS,$level);

    $response = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if( $code != 200 )
    {
        exit("Openhab is down. Can't inform openhab about system status.");
    }
}
else
{
    exit("Netdata is down. Can't inform openhab about system status.");
}
