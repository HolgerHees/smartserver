<?php
require "config.php";

if( file_exists($system_state_file) )
{
    $data = file_get_contents($system_state_file);
    $data = json_decode($data);
}
else
{
    $data = array();
}
   
# test data
#$data->os_outdated[] = (object) ["pid" => 1, "ppid" => 2, "uid" => 3, "user" => "hhees", "command" => "test", "service" => "device_ping" ];
#$data->os_updates[] = (object) ["name" => "test", "current" => "1.0", "update" => "2.0", "arch" => "x86_64" ];

$needs_system_reboot = false;
$service_restarts = [];
foreach( $data->os_outdated as $outdate)
{
    if( empty($outdate->service) ) $needs_system_reboot = true;
    else $service_restarts[] = $outdate->service;
}

$last_system_state = date_create($data->last_system_state);
$last_system_state->setTimezone(new DateTimeZone('Europe/Berlin'));
$last_system_state_fmt = $last_system_state->format("d.m.Y H:i");
    
$last_system_update = date_create($data->last_system_update);
$last_system_update->setTimezone(new DateTimeZone('Europe/Berlin'));
$last_system_update_fmt = $last_system_update->format("d.m.Y H:i");

$last_deployment_update = date_create($data->last_deployment_update);
$last_deployment_update->setTimezone(new DateTimeZone('Europe/Berlin'));
$last_deployment_update_fmt = $last_deployment_update->format("d.m.Y H:i");

$last_update = $last_system_state;
if( $last_system_update < $last_update ) $last_update = $last_system_update;
if( $last_deployment_update < $last_update ) $last_update = $last_deployment_update;
$last_update_fmt = $last_update->format("d.m.Y H:i");

if( $data->os_reboot || $needs_system_reboot )
{ 
    $rebootNeeded = "<div class=\"info red\">Reboot needed (";
    $reason = [];
    if( $data->os_reboot ) $reason[] = "installed core updates";
    if( $needs_system_reboot ) $reason[] = "outdated processes";
    $rebootNeeded .= implode(", ", $reason);
    $rebootNeeded .= ")</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.action(this,'systemReboot',null,true)\">Reboot system</div></div>";
}
else
{
    $rebootNeeded = "";
}

if( count($data->os_outdated) > 0 )
{

    $systemState = "<div class=\"info\">System has " . count($data->os_outdated) . " outdated processes" . ( $last_update_fmt != $last_system_state_fmt ? " " . $last_system_state_fmt : "" ) . "</div><div class=\"buttons\">";
    if(count($service_restarts)>0) $systemState .= "<div class=\"form button yellow\" onclick=\"mx.UNCore.action(this,'restartService','" . implode(",",$service_restarts) . "',true)\">Restart services</div>";
    $systemState .= "<div class=\"form button toggle\" id=\"systemProcesses\" onclick=\"mx.UNCore.toggle(this,'systemStateDetails')\"></div></div>";
    
    error_log($systemState);

    $systemStateDetails = "<div class=\"row\">
          <div>PID</div>
          <div>PPID</div>
          <div>UID</div>
          <div>User</div>
          <div class=\"grow\">Command</div>
          <div class=\"grow\">Service</div>
          <div></div>
        </div>";
    foreach( $data->os_outdated as $outdate)
    {
        $systemStateDetails .= "<div class=\"row\">";
        $systemStateDetails .= "<div>" . $outdate->pid . "</div>";
        $systemStateDetails .= "<div>" . $outdate->ppid . "</div>";
        $systemStateDetails .= "<div>" . $outdate->uid . "</div>";
        $systemStateDetails .= "<div>" . $outdate->user . "</div>";
        $systemStateDetails .= "<div>" . $outdate->command . "</div>";
        $systemStateDetails .= "<div>" . $outdate->service . "</div>";
        $systemStateDetails .= "<div>" . ( $outdate->service ? "<div class=\"form button yellow\" onclick=\"mx.UNCore.action(this,'restartService','" . $outdate->service . "',true)\">Restart</div>" : "" ) . "</div>";
        $systemStateDetails .= "</div>";
    }
}
else
{
    $systemState = "<div class=\"info green\">No outdates processes</div>";
    $systemStateDetails = "";
}

if( count($data->os_updates) > 0 )
{
    $systemUpdate = "<div class=\"info\">" . count($data->os_updates) . " System updates " . ( $last_update_fmt != $last_system_update_fmt ? " " . $last_system_update_fmt : "" ) . "</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.action(this,'installSystemUpdates',null,true)\">Install updates</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'systemUpdateDetails')\"></div></div>";

    $systemUpdateDetails = "<div class=\"row\">
          <div>Name</div>
          <div>Current</div>
          <div class=\"grow\">Update</div>
          <div>Arch</div>
        </div>";
    foreach( $data->os_updates as $update)
    {
        $systemUpdateDetails .= "<div class=\"row\">";
        $systemUpdateDetails .= "<div>" . $update->name . "</div>";
        $systemUpdateDetails .= "<div>" . $update->current . "</div>";
        $systemUpdateDetails .= "<div>" . $update->update . "</div>";
        $systemUpdateDetails .= "<div>" . $update->arch . "</div>";
        $systemUpdateDetails .= "</div>";
    }
}
else
{
    $systemUpdate = "<div class=\"info green\">No system updates available " . ( $last_update_fmt != $last_system_update_fmt ? " " . $last_system_update_fmt : "") . "</div>";
    $systemUpdateDetails = "";
}

if( count($data->smartserver_changes) > 0 )
{
    $deploymentUpdate = "<div class=\"info\">" . count($data->smartserver_changes) . " Deployment updates " . ( $last_update_fmt != $last_deployment_update_fmt ? " " . $last_deployment_update_fmt : "" ) . "</div><div class=\"buttons\"><div class=\"form button red\" onclick=\"mx.UNCore.actionSmartserverUpdateDialog(this,'deploySmartserverUpdates')\">Deploy updates</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'deploymentUpdateDetails')\"></div></div>";

    $deploymentUpdateDetails = "<div class=\"row\">
          <div>Flag</div>
          <div class=\"grow\">File</div>
        </div>";
    foreach( $data->smartserver_changes as $update)
    {
        $deploymentUpdateDetails .= "<div class=\"row\">";
        $deploymentUpdateDetails .= "<div>" . $update->flag . "</div>";
        $deploymentUpdateDetails .= "<div>" . $update->path . "</div>";
        $deploymentUpdateDetails .= "</div>";
        #$last_deployment_update = date_create();
        #break;
    }
}
else
{
    $deploymentUpdate = "<div class=\"info green\">No deployment updates available" . ( $last_update_fmt != $last_deployment_update_fmt ? " " . $last_deployment_update_fmt : "") . "</div>";
    $deploymentUpdateDetails = "";
}

echo "<div id=\"lastUpdates\">Last full refresh " . $last_update_fmt . "</div>";

echo "<div id=\"rebootNeeded\">" . $rebootNeeded . "</div>";
echo "<div id=\"systemState\">" . $systemState . "</div>";
echo "<div id=\"systemStateDetails\">" . $systemStateDetails . "</div>";
echo "<div id=\"systemStateTimestamp\">" . $last_system_state->getTimestamp() . "</div>";

echo "<div id=\"systemUpdate\">" . $systemUpdate . "</div>";
echo "<div id=\"systemUpdateDetails\">" . $systemUpdateDetails . "</div>";
echo "<div id=\"systemUpdateTimestamp\">" . $last_system_update->getTimestamp() . "</div>";

echo "<div id=\"deploymentUpdate\">" . $deploymentUpdate . "</div>";
echo "<div id=\"deploymentUpdateDetails\">" . $deploymentUpdateDetails . "</div>";
echo "<div id=\"deploymentUpdateTimestamp\">" . $last_deployment_update->getTimestamp() . "</div>";
