<?php
include __DIR__ . "/../config.php";
include __DIR__ . "/../inc/Preview.php";

if( empty($argv[1]) || ( $argv[1] != "clean" && $argv[1] != "generate" ) )
{
    die("Missing or wrong parameter 'cmd' <clean|generate>");
}

$cmd = $argv[1];

if( $cmd == "clean" )
{
    $result = shell_exec("find " . CACHE_DIRECTORY . " -maxdepth 2 -mmin +" . MAX_PREVIEW_AGE . " -type f -name '*.jpg'");
    $lines = explode(PHP_EOL, $result);
    foreach( $lines as $line )
    {
        if( empty($line) ) continue;

        unlink($line);
    }
}
else
{
    //$result = shell_exec("find " . FTP_FOLDER . " -maxdepth 2 -mmin -5760 -type f -name '*.jpg'");
    $cmd = "find " . FTP_FOLDER . " -maxdepth 2 -readable " . ( !empty($argv[2]) && $argv[2] == "full" ? "" : "-mmin -120 " ) . "-type f -name '*.jpg' 2>/dev/null";
    //echo $cmd;
    $result = shell_exec($cmd);

    $lines = explode(PHP_EOL, $result);
    foreach( $lines as $line )
    {
        if( empty($line) ) continue;

        Preview::check($line);
    }
}

