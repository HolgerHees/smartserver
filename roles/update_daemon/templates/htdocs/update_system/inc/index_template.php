<?php
class IndexTemplate
{
    private static $deploymentUpdateInfoCodes = array(
        "failed" => ["red","Skipped git pull because of broken remote ci tests"],
        "pending" => ["yellow","Skipped git pull because of some remote ci pending"],
        "pulled_tested" => ["green", "Git pulled and all remote ci succeeded"],
        "pulled" => ["green", "Git pulled"],
        "uncommitted" => ["red","Skipped git pull because of has uncommitted changes"]
    );

    private static function extractDate($data,$key)
    {
        if( isset($data[$key]) )
        {
            $date = date_create($data[$key]);
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

    public static function getDeploymentEncryptionState($deployment_state_file)
    {
        $deployment_data = array();
        if( file_exists($deployment_state_file) )
        {
            $deployment_data = file_get_contents($deployment_state_file);
            $deployment_data = json_decode($deployment_data,true);
        }
        $has_encrypted_vault = isset($deployment_data["has_encrypted_vault"]) ? $deployment_data["has_encrypted_vault"] : false;
        
        return $has_encrypted_vault;
    }

    public static function getDeploymentTags($deployment_tags_file)
    {
        $deployment_tags = array();
        if( file_exists($deployment_tags_file) )
        {
            $deployment_tags = file_get_contents($deployment_tags_file);
            $deployment_tags = json_decode($deployment_tags,true);
        }
        $smartserver_tags = implode(",", $deployment_tags);
  
        return $smartserver_tags;
    }
    
    public static function getSystemData($system_state_file)
    {
        $system_data = array();

        if( file_exists($system_state_file) )
        {
            $system_data = file_get_contents($system_state_file);
            $system_data = json_decode($system_data,true);
        }
      
        # test data
        #$system_data["os_outdated"][] = ["pid" => 1, "ppid" => 2, "uid" => 3, "user" => "hhees", "command" => "test", "service" => "device_ping" ];
        #$system_data["os_outdated"][] = ["pid" => 1, "ppid" => 2, "uid" => 3, "user" => "hhees", "command" => "test1", "service" => "" ];
        #$system_data["os_updates"][] = ["name" => "test", "current" => "1.0", "update" => "2.0", "arch" => "x86_64" ];
        return $system_data;
    }

    public static function getJobs($deployment_logs_folder)
    {
        $jobs = Job::getJobs($deployment_logs_folder);
        $jobs = array_values(array_filter($jobs, function($job){ return $job->getState() != "running"; }));

        if( count($jobs) > 0 )
        {
            $last_job = $jobs[0];
            
            $is_successful = $last_job->getState() == "success";
            
            $state_msg = $is_successful ? "was successful" : "failed";
            $color = $is_successful ? "" : " red";
            
            $last_running_jobs_msg = "<div class=\"info" . $color . "\">Last '<div class=\"detailView\" onclick=\"mx.UNCore.openDetails(this,'" . $last_job->getDateTime()->format('Y.m.d_H.i.s') . "','" . $last_job->getCmd() . "','" . $last_job->getUsername() . "')\">" . $last_job->getCmd() . "</div>' " . $state_msg . " after " . $last_job->getDuration() . " seconds</div><div class=\"buttons\"><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'lastRunningJobsDetails')\"></div></div>";

            $last_running_jobs_details_msg = "<div class=\"row\">
                  <div></div>
                  <div class=\"grow\">Cmd</div>
                  <div>Username</div>
                  <div>State</div>
                  <div>Duration</div>
                  <div>Date</div>
                </div>";
            foreach( $jobs as $job)
            {
                $last_running_jobs_details_msg .= "<div class=\"row\" onclick=\"mx.UNCore.openDetails(this,'" . $job->getDateTime()->format('Y.m.d_H.i.s') . "','" . $job->getCmd() . "','" . $job->getUsername() . "')\">";
                $last_running_jobs_details_msg .= "<div class=\"state " . $job->getState() . "\"></div>";
                $last_running_jobs_details_msg .= "<div>" . $job->getCmd() . "</div>";
                $last_running_jobs_details_msg .= "<div>" . $job->getUsername() . "</div>";
                $last_running_jobs_details_msg .= "<div>" . LogFile::formatState($job->getState()) . "</div>";
                $last_running_jobs_details_msg .= "<div>" . ( explode(".", LogFile::formatDuration($job->getDuration()))[0] ) . "</div>";
                $last_running_jobs_details_msg .= "<div class=\"indexLogDate\">" . $job->getDateTime()->format('d.m.Y H:i:s') . "</div>";
                $last_running_jobs_details_msg .= "</div>";
                #break;
            }
        }
        else
        {
            $last_running_jobs_msg = "<div class=\"info green\">No job history</div>";
            $last_running_jobs_details_msg = "";
        }
        
        return [ $last_running_jobs_msg, $last_running_jobs_details_msg ];
    }
    
    public static function getSystemState($system_data, $service_restarts)
    {
        if( isset($system_data["os_outdated"]) && count($system_data["os_outdated"]) > 0 )
        {

            $system_state_msg = "<div class=\"info\">" . count($system_data["os_outdated"]) . " outdated processe" . ( $system_data["os_outdated"] > 1 ? 's' : '' ) . "</div><div class=\"buttons\">";
            if(count($service_restarts)>0) $system_state_msg .= "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . implode(",",$service_restarts) . "\">Restart all</div>";
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
                $system_state_details_msg .= "<div>" . ( $outdate["service"] ? "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . $outdate["service"] . "\">Restart</div>" : "" ) . "</div>";
                $system_state_details_msg .= "</div>";
            }
        }
        else
        {
            $system_state_msg = "<div class=\"info\">No outdates processes</div>";
            $system_state_details_msg = "";
        }
        
        return [ $system_state_msg, $system_state_details_msg ];
    }
    
    public static function getSystemUpdate($system_data)
    {
        $updates_are_available = 0;
        if( isset($system_data["os_updates"]) && count($system_data["os_updates"]) > 0 )
        {
            $updates_are_available = count($system_data["os_updates"]);
            $system_update_msg = "<div class=\"info\">" . count($system_data["os_updates"]) . " updates available</div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UNCore.actionInstallUpdates(this)\">Install</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'systemUpdateDetails')\"></div></div>";

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
            $system_update_msg = "<div class=\"info\">No updates available</div>";
            $system_update_details = "";
        }
        
        return [ $updates_are_available, $system_update_msg, $system_update_details ];
    }
       
    public static function getDeploymentUpdate($system_data)
    {
        $updates_are_available = 0;
        if( isset($system_data["smartserver_changes"]) && count($system_data["smartserver_changes"]) > 0 )
        {
            $updates_are_available = count($system_data["smartserver_changes"]) > 0;
            $deployment_update_msg = "<div class=\"info\">" . count($system_data["smartserver_changes"]) . " updates available</div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UNCore.actionDeployUpdates(this)\">Install</div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'deploymentUpdateDetails')\"></div></div>";

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
            $deployment_update_msg = "<div class=\"info\">No updates available</div>";
            $deployment_update_details_msg = "";
        }
        
        return [ $updates_are_available, $deployment_update_msg, $deployment_update_details_msg ];
    }
    
    public static function getWorkflow($last_update,$system_update_available,$deployment_update_available)
    {
        $now = new DateTime();
        $timeout = 300;
        
        if( $system_update_available > 0 || $deployment_update_available > 0 )
        {
            $types = [];
            if( $system_update_available ) $types[] = $system_update_available . " system update" . ( $system_update_available > 1 ? 's' : '' );
            if( $deployment_update_available ) $types[] = $deployment_update_available . " smartserver update" . ( $deployment_update_available > 1 ? 's' : '' );
          
            $msg = "There " . ( $system_update_available + $deployment_update_available > 1 ? "are" : "is" ) . " " . implode(" and ",$types) . " available";
            
            $workflow_fallback_msg = "<div class=\"info\">" . $msg . "<div class=\"sub\">Currently disabled because it is only possible max. 5 minutes after a system status refresh</div></div><div class=\"buttons\"><div class=\"form button exclusive disabled blocked green\" onclick=\"mx.UNCore.actionUpdateWorkflow(this)\">Install all</div></div>";

            if( $now->getTimestamp() - $last_update->getTimestamp() > $timeout )
            {
                $workflow_msg = $workflow_fallback_msg;
                $workflow_fallback_msg = "";
            }
            else
            {                                
                $workflow_msg = "<div class=\"info\">" . $msg . "</div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UNCore.actionUpdateWorkflow(this)\">Update all</div></div>";
            }
        }
        else
        {
            $workflow_msg = "";
            $workflow_fallback_msg = "";
        }
        
        return [ $workflow_msg, $workflow_fallback_msg, $timeout ];
    }

    public static function getServiceOrRebootState($system_data)
    {
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
            $reboot_needed_msg = "<div class=\"info red\">Reboot needed";
            $reason = [];
            if( $system_data["os_reboot"] ) $reason[] = "installed core updates";
            if( $needs_system_reboot ) $reason[] = "outdated processes";
            $reboot_needed_msg .= "<div class=\"sub\">Is needed because of " . implode(", ", $reason) . "</div>";
            $reboot_needed_msg .= "</div><div class=\"buttons\"><div class=\"form button exclusive red\" onclick=\"mx.UNCore.actionRebootSystem(this)\">Reboot system</div></div>";
        }
        
        return [ $service_restarts, $reboot_needed_msg ];
    }
    
    public static function getDeploymentCheckState($system_data)
    {
        list(, $last_smartserver_pull_fmt, ) = IndexTemplate::extractDate($system_data, "smartserver_pull");
        $deployment_update_code = isset($system_data["smartserver_code"]) ? $system_data["smartserver_code"] : "";
        
        list($colorClass,$updateMsg) = IndexTemplate::$deploymentUpdateInfoCodes[$deployment_update_code];
        
        return "<div class=\"info " . $colorClass . "\">" . $updateMsg . "<div class=\"sub\">Last git pull was on " .$last_smartserver_pull_fmt . "</div></div>";
    }
    
    public static function dump($system_state_file,$deployment_state_file,$deployment_tags_file,$deployment_logs_folder,$forced_data)
    {
        #error_log(print_r($forced_data));
        #error_log(in_array("system_updates.state",$forced_data));
      
        $result = "<div id=\"data\" style=\"display:none\">";
            
        if( $forced_data == null or in_array("system_updates.state",$forced_data) )
        {
            $system_data = IndexTemplate::getSystemData($system_state_file);   

            list($last_system_state, $last_system_state_fmt, $last_system_state_timestamp) = IndexTemplate::extractDate($system_data, "last_system_state");
            list($last_system_update, $last_system_update_fmt, $last_system_update_timestamp) = IndexTemplate::extractDate($system_data, "last_system_update");
            list($last_deployment_update, $last_deployment_update_fmt, $last_deployment_update_timestamp) = IndexTemplate::extractDate($system_data, "last_deployment_update");

            $last_update = $last_system_state;
            if( $last_system_update < $last_update ) $last_update = $last_system_update;
            if( $last_deployment_update < $last_update ) $last_update = $last_deployment_update;
            $last_update_fmt = $last_update->format("d.m.Y H:i");

            $result .= "<div class=\"lastUpdateDateFormatted\">" . $last_update_fmt . "</div>";

            list( $service_restarts, $reboot_needed_msg ) = IndexTemplate::getServiceOrRebootState($system_data);
            $result .= "<div class=\"systemRebootState\">" . $reboot_needed_msg . "</div>";

            list($system_state_msg,$system_state_details_msg) = IndexTemplate::getSystemState($system_data, $service_restarts);
            $result .= "<div class=\"systemStateHeader\">" . $system_state_msg . "</div>";
            $result .= "<div class=\"systemStateDetails\">" . $system_state_details_msg . "</div>";
            $result .= "<div class=\"systemStateDateAsTimestamp\">" . $last_system_state_timestamp . "</div>";
            $result .= "<div class=\"systemStateDateFormatted\">" . $last_system_state_fmt . "</div>";

            list($system_updates_available,$system_update_msg,$system_update_details) = IndexTemplate::getSystemUpdate($system_data);
            $result .= "<div class=\"systemUpdateHeader\">" . $system_update_msg . "</div>";
            $result .= "<div class=\"systemUpdateDetails\">" . $system_update_details . "</div>";
            $result .= "<div class=\"systemUpdateDateAsTimestamp\">" . $last_system_update_timestamp . "</div>";
            $result .= "<div class=\"systemUpdateDateFormatted\">" . $last_system_update_fmt . "</div>";

            list($deployment_updates_available,$deployment_update_msg,$deployment_update_details_msg) = IndexTemplate::getDeploymentUpdate($system_data);
            $result .= "<div class=\"deploymentUpdateHeader\">" . $deployment_update_msg . "</div>";
            $result .= "<div class=\"deploymentUpdateDetails\">" . $deployment_update_details_msg . "</div>";
            $result .= "<div class=\"deploymentUpdateDateAsTimestamp\">" . $last_deployment_update_timestamp . "</div>";
            $result .= "<div class=\"deploymentUpdateDateFormatted\">" . $last_deployment_update_fmt . "</div>";

            $deployment_state_msg = IndexTemplate::getDeploymentCheckState($system_data);
            $result .= "<div class=\"deploymentUpdateState\">" . $deployment_state_msg . "</div>";
            
            list( $update_workflow_msg, $update_workflow_fallback_msg, $workflow_timeout ) = IndexTemplate::getWorkflow($last_update,$system_updates_available,$deployment_updates_available);
            $result .= "<div class=\"updateWorkflow\">" . $update_workflow_msg . "</div>";
            $result .= "<div class=\"updateWorkflowFallback\">" . $update_workflow_fallback_msg . "</div>";
            $result .= "<div class=\"updateWorkflowTimeout\">" . $workflow_timeout . "</div>";
        }
        
        if( $forced_data == null or in_array("job.state",$forced_data) )
        {
            list($last_running_jobs_msg,$last_running_jobs_details_msg) = IndexTemplate::getJobs($deployment_logs_folder);
            $result .= "<div class=\"lastRunningJobsHeader\">" . $last_running_jobs_msg . "</div>";
            $result .= "<div class=\"lastRunningJobsDetails\">" . $last_running_jobs_details_msg . "</div>";
        }
        
        if( $forced_data == null or in_array("deployment.state",$forced_data) )
        {
            $result .= "<div class=\"hasEncryptedVault\">" . ( IndexTemplate::getDeploymentEncryptionState($deployment_state_file) ? 1 : 0 ) . "</div>";
        }
        
        if( $forced_data == null or in_array("deployment.tags",$forced_data) )
        {
            $result .= "<div class=\"deploymentTags\">" . IndexTemplate::getDeploymentTags($deployment_tags_file) . "</div>";
        }
        
        $result .= "</div>";
        
        return $result;
    }
}
