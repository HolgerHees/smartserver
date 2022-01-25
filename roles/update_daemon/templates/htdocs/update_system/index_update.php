<?php
require "config.php";

function extractDate($data,$key)
{
    if( isset($data["last_system_state"]) )
    {
        $date = date_create($data["last_system_state"]);
        $date->setTimezone(new DateTimeZone('Europe/Berlin'));
        $date_fmt = $date->format("d.m.Y H:i");
        $date_timestamp = $date->getTimestamp();
    }
    else
    { 
        $date = date_create();
        $date_fmt = "";
        $date_timestamp = 0;
    }
    
    return array($date, $date_fmt, $date_timestamp);
}

$deployment_data = array();
$system_data = array();

if( file_exists($deployment_state_file) )
{
    $deployment_data = file_get_contents($deployment_state_file);
    $deployment_data = json_decode($deployment_data,true);
}

if( file_exists($system_state_file) )
{
    $system_data = file_get_contents($system_state_file);
    $system_data = json_decode($system_data,true);
}
   
# test data
#$system_data["os_outdated[] = (object) ["pid" => 1, "ppid" => 2, "uid" => 3, "user" => "hhees", "command" => "test", "service" => "device_ping" ];
#$system_data["os_outdated[] = (object) ["pid" => 1, "ppid" => 2, "uid" => 3, "user" => "hhees", "command" => "test1", "service" => "" ];
#$system_data["os_updates[] = (object) ["name" => "test", "current" => "1.0", "update" => "2.0", "arch" => "x86_64" ];

$has_encrypted_vault = isset($deployment_data["has_encrypted_vault"]) ? $deployment_data["has_encrypted_vault"] : false;

list($last_system_state, $last_system_state_fmt, $last_system_state_timestamp) = extractDate($system_data, "last_system_state");
list($last_system_update, $last_system_update_fmt, $last_system_update_timestamp) = extractDate($system_data, "last_system_update");
list($last_deployment_update, $last_deployment_update_fmt, $last_deployment_update_timestamp) = extractDate($system_data, "last_deployment_update");

$last_update = $last_system_state;
if( $last_system_update < $last_update ) $last_update = $last_system_update;
if( $last_deployment_update < $last_update ) $last_update = $last_deployment_update;
$last_update_fmt = $last_update->format("d.m.Y H:i");

list(, $last_smartserver_pull_fmt, ) = extractDate($system_data, "smartserver_pull");

$deployment_update_code = isset($system_data["smartserver_code"]) ? $system_data["smartserver_code"] : "";
$smartserver_tags = isset($system_data["smartserver_tags"]) ? implode(",", $system_data["smartserver_tags"]) : "";

$needs_system_reboot = false;
$service_restarts = [];
if( isset($system_data["os_outdated"]) )
{
    foreach( $system_data["os_outdated"] as $outdate)
    {
        if( empty($outdate["service"]) ) $needs_system_reboot = true;
        else $service_restarts[] = $outdate["service"];
    }
}

$reboot_needed_msg = "";
if( isset($system_data["os_reboot"]) && ( $system_data["os_reboot"] || $needs_system_reboot ) )
{ 
    $reboot_needed_msg = "<div class=\"info red\">Reboot needed (";
    $reason = [];
    if( $system_data["os_reboot"] ) $reason[] = "installed core updates";
    if( $needs_system_reboot ) $reason[] = "outdated processes";
    $reboot_needed_msg .= implode(", ", $reason);
    $reboot_needed_msg .= ")</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.actionRebootSystem(this)\">Reboot system</div></div>";
}

if( isset($system_data["os_outdated"]) && count($system_data["os_outdated"]) > 0 )
{

    $system_state_msg = "<div class=\"info\">System has " . count($system_data["os_outdated"]) . " outdated processes</div><div class=\"buttons\">";
    if(count($service_restarts)>0) $system_state_msg .= "<div class=\"form button yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . implode(",",$service_restarts) . "\">Restart services</div>";
    $system_state_msg .= "<div class=\"form button toggle\" id=\"systemProcesses\" onclick=\"mx.UNCore.toggle(this,'systemStateDetails')\"></div></div>";

    $system_state_details_msg = "<div class=\"row\">
          <div>PID</div>
          <div>PPID</div>
          <div>UID</div>
          <div>User</div>
          <div class=\"grow\">Command</div>
          <div class=\"grow\">Service</div>
          <div></div>
        </div>";
    foreach( $system_data["os_outdated"] as $outdate)
    {
        $system_state_details_msg .= "<div class=\"row\">";
        $system_state_details_msg .= "<div>" . $outdate["pid"] . "</div>";
        $system_state_details_msg .= "<div>" . $outdate["ppid"] . "</div>";
        $system_state_details_msg .= "<div>" . $outdate["uid"] . "</div>";
        $system_state_details_msg .= "<div>" . $outdate["user"] . "</div>";
        $system_state_details_msg .= "<div>" . $outdate["command"] . "</div>";
        $system_state_details_msg .= "<div>" . $outdate["service"] . "</div>";
        $system_state_details_msg .= "<div>" . ( $outdate["service"] ? "<div class=\"form button yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . $outdate["service"] . "\">Restart</div>" : "" ) . "</div>";
        $system_state_details_msg .= "</div>";
    }
}
else
{
    $system_state_msg = "<div class=\"info green\">No outdates processes</div>";
    $system_state_details_msg = "";
}

if( isset($system_data["os_updates"]) && count($system_data["os_updates"]) > 0 )
{
    $system_update_msg = "<div class=\"info\">" . count($system_data["os_updates"]) . " System updates</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.actionInstallUpdates(this)\">Install updates</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'systemUpdateDetails')\"></div></div>";

    $system_update_details = "<div class=\"row\">
          <div>Name</div>
          <div>Current</div>
          <div class=\"grow\">Update</div>
          <div>Arch</div>
        </div>";
    foreach( $system_data["os_updates"] as $update)
    {
        $system_update_details .= "<div class=\"row\">";
        $system_update_details .= "<div>" . $update["name"] . "</div>";
        $system_update_details .= "<div>" . $update["current"] . "</div>";
        $system_update_details .= "<div>" . $update["update"] . "</div>";
        $system_update_details .= "<div>" . $update["arch"] . "</div>";
        $system_update_details .= "</div>";
    }
}
else
{
    $system_update_msg = "<div class=\"info green\">No system updates available</div>";
    $system_update_details = "";
}

if( isset($system_data["smartserver_changes"]) && count($system_data["smartserver_changes"]) > 0 )
{
    $deployment_update_msg = "<div class=\"info\">" . count($system_data["smartserver_changes"]) . " Deployment updates</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.actionDeployUpdates(this)\">Deploy updates</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'deploymentUpdateDetails')\"></div></div>";

    $deployment_update_details_msg = "<div class=\"row\">
          <div>Flag</div>
          <div class=\"grow\">File</div>
        </div>";
    foreach( $system_data["smartserver_changes"] as $update)
    {
        $deployment_update_details_msg .= "<div class=\"row\">";
        $deployment_update_details_msg .= "<div>" . $update["flag"] . "</div>";
        $deployment_update_details_msg .= "<div>" . $update["path"] . "</div>";
        $deployment_update_details_msg .= "</div>";
        #$last_deployment_update = date_create();
        #break;
    }
}
else
{
    $deployment_update_msg = "<div class=\"info green\">No deployment updates available</div>";
    $deployment_update_details_msg = "";
}

echo "<div id=\"hasEncryptedVault\">" . ( $has_encrypted_vault ? 1 : 0 ) . "</div>";
echo "<div id=\"lastUpdateDateFormatted\">" . $last_update_fmt . "</div>";

echo "<div id=\"systemRebootNeeded\">" . $reboot_needed_msg . "</div>";

echo "<div id=\"systemStateHeader\">" . $system_state_msg . "</div>";
echo "<div id=\"systemStateDetails\">" . $system_state_details_msg . "</div>";
echo "<div id=\"systemStateDateAsTimestamp\">" . $last_system_state_timestamp . "</div>";
echo "<div id=\"systemStateDateFormatted\">" . $last_system_state_fmt . "</div>";

echo "<div id=\"systemUpdateHeader\">" . $system_update_msg . "</div>";
echo "<div id=\"systemUpdateDetails\">" . $system_update_details . "</div>";
echo "<div id=\"systemUpdateDateAsTimestamp\">" . $last_system_update_timestamp . "</div>";
echo "<div id=\"systemUpdateDateFormatted\">" . $last_system_update_fmt . "</div>";

echo "<div id=\"deploymentUpdateHeader\">" . $deployment_update_msg . "</div>";
echo "<div id=\"deploymentUpdateDetails\">" . $deployment_update_details_msg . "</div>";
echo "<div id=\"deploymentUpdateDateAsTimestamp\">" . $last_deployment_update_timestamp . "</div>";
echo "<div id=\"deploymentUpdateDateFormatted\">" . $last_deployment_update_fmt . "</div>";

echo "<div id=\"deploymentUpdateLastPullDate\">" . $last_smartserver_pull_fmt . "</div>";
echo "<div id=\"deploymentUpdateStatusCode\">" . $deployment_update_code . "</div>";

echo "<div id=\"deploymentTags\">" . $smartserver_tags . "</div>";
