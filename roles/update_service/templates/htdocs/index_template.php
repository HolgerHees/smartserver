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

    private static function extractFileDate($file)
    {
        $date_timestamp = filemtime($file);
        $date = (date_create())->setTimestamp($date_timestamp);
        $date->setTimezone(new DateTimeZone('Europe/Berlin'));
        $date_fmt = $date->format("d.m.Y H:i");
        
        return array($date, $date_fmt, $date_timestamp);
    }

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
        #$system_data["smartserver_outdated"][] = "netdata";
        return $system_data;
    }
    
    public static function getOutdatedRolesData($outdated_roles_state_file)
    {
        $roles_data = array();

        if( file_exists($outdated_roles_state_file) )
        {
            $roles_data = file_get_contents($outdated_roles_state_file);
            $roles_data = json_decode($roles_data,true);
        }
      
        return $roles_data;
    }

    public static function getJobs($deployment_logs_folder)
    {
        $jobs = Job::getJobs($deployment_logs_folder);
        $jobs = array_values(array_filter($jobs, function($job){ return $job->getState() != "running"; }));

        if( count($jobs) > 0 )
        {
            $last_job = $jobs[0];
            
            $is_failed = $last_job->getState() == "failed";

            $action_msg = "<div class=\"detailView\" onclick=\"mx.UNCore.openDetails(this,'" . $last_job->getDateTime()->format('Y.m.d_H.i.s') . "','" . $last_job->getCmd() . "','" . $last_job->getUsername() . "')\">" . $last_job->getCmd() . "</div>";
            $action_msg = I18N::escapeAttribute($action_msg);
            
            $state_msg = $is_failed ? "failed" : ( $last_job->getState() == "success" ? "was successful" : "was stopped" );
            $color = $is_failed ? " red" : "";
            
            $last_running_jobs_msg = "<div class=\"info" . $color . "\"";
            $last_running_jobs_msg .= " data-i18n=\"Last '{1}' {2} after {3} seconds\"";
            $last_running_jobs_msg .= " data-i18n_1=\"" . $action_msg . "\"";
            $last_running_jobs_msg .= " data-i18n_2_key=\"" . $state_msg . "\"";
            $last_running_jobs_msg .= " data-i18n_3=\"" . $last_job->getDuration() . "\"";
            $last_running_jobs_msg .= ">";
            
            $last_running_jobs_msg .= "</div><div class=\"buttons\"><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'lastRunningJobsDetails')\"></div></div>";

            $last_running_jobs_details_msg = "<div class=\"row\">
                  <div></div>
                  <div class=\"grow\" data-i18n=\"Job\"></div>
                  <div data-i18n=\"User\"></div>
                  <div data-i18n=\"State\"></div>
                  <div data-i18n=\"Duration\"></div>
                  <div data-i18n=\"Date\"></div>
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
            $last_running_jobs_msg = "<div class=\"info green\" data-i18n=\"No job history available\"></div>";
            $last_running_jobs_details_msg = "";
        }
        
        return [ $last_running_jobs_msg, $last_running_jobs_details_msg ];
    }
    
    public static function getSystemState($system_data, $service_restarts, $roles_data)
    {
        if( isset($system_data["os_outdated"]) && count($system_data["os_outdated"]) > 0 )
        {
            $count = count($system_data["os_outdated"]);
            $plural = $count > 1;
          
            $i18n_main_msg = $plural ? "{} outdated processes" : "{} outdated process";
            $i18n_info_msg = $plural ? "through a system update which affects these processes" : "through a system update which affects these process";
            
            $system_state_msg = "<div class=\"info\"><span data-i18n=\"" . $i18n_main_msg . "\" data-i18n_1=\"" . $count . "\"></span><div class=\"sub\" data-i18n=\"" . $i18n_info_msg . "\"></div></div><div class=\"buttons\">";
            if(count($service_restarts)>0) $system_state_msg .= "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . implode(",",$service_restarts) . "\" data-i18n=\"Restart all\"></div>";
            $system_state_msg .= "<div class=\"form button toggle\" id=\"systemProcesses\" onclick=\"mx.UNCore.toggle(this,'systemStateDetails')\"></div></div>";

            $system_state_details_msg = "<div class=\"row\">
                  <div data-i18n=\"PID\"></div>
                  <div data-i18n=\"PPID\"></div>
                  <div data-i18n=\"UID\"></div>
                  <div data-i18n=\"User\"></div>
                  <div class=\"grow\" data-i18n=\"Command\"></div>
                  <div class=\"grow\" data-i18n=\"Service\"></div>
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
                $system_state_details_msg .= "<div>" . ( $outdate["service"] ? "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionRestartServices(this)\" data-service=\"" . $outdate["service"] . "\" data-i18n=\"Restart\"></div>" : "" ) . "</div>";
                $system_state_details_msg .= "</div>";
            }
        }
        else
        {
            $system_state_msg = "<div class=\"info\" data-i18n=\"There are no outdated processes running\"></div>";
            $system_state_details_msg = "";
        }
        
        if( count($roles_data) > 0 )
        {
            $count = count($roles_data);
            $plural = $count > 1;
          
            $i18n_main_msg = $plural ? "{} overwritten smartserver roles" : "{} overwritten smartserver role";
            $i18n_info_msg = $plural ? "through a system update which affects these roles" : "through a system update which affects these role";

            $role_state_msg = "<div class=\"info\"><span data-i18n=\"" . $i18n_main_msg . "\" data-i18n_1=\"" . $count . "\"></span><div class=\"sub\" data-i18n=\"" . $i18n_info_msg . "\"></div></div><div class=\"buttons\">";
            $role_state_msg .= "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionDeployUpdates(this)\" data-tag=\"" . implode(",",$roles_data) . "\" data-i18n=\"Install all\"></div>";
            $role_state_msg .= "<div class=\"form button toggle\" id=\"smartserverRoles\" onclick=\"mx.UNCore.toggle(this,'roleStateDetails')\"></div></div>";

            $role_state_details_msg = "<div class=\"row\">
                  <div class=\"grow\">Role</div>
                  <div></div>
                </div>";
            foreach( $roles_data as $outdate)
            {
                $role_state_details_msg .= "<div class=\"row\">";
                $role_state_details_msg .= "<div>" . $outdate . "</div>";
                $role_state_details_msg .= "<div>" . ( $outdate ? "<div class=\"form button exclusive yellow\" onclick=\"mx.UNCore.actionDeployUpdates(this)\" data-tag=\"" . $outdate . "\" data-i18n=\"Install\"></div>" : "" ) . "</div>";
                $role_state_details_msg .= "</div>";
            }
        }
        else
        {
            $role_state_msg = "<div class=\"info\" data-i18n=\"There are no outdated roles\"></div>";
            $role_state_details_msg = "";
        }
        
        if( !$role_state_details_msg && !$system_state_details_msg )
        {
            $system_state_msg = "<div class=\"info\" data-i18n=\"There are no outdated processes or roles running\"></div>";
            $role_state_msg = "";
        }

        return [ $system_state_msg, $system_state_details_msg, $role_state_msg, $role_state_details_msg ];
    }

    public static function getSystemUpdate($system_data)
    {
        $updates_are_available = 0;
        if( isset($system_data["os_updates"]) && count($system_data["os_updates"]) > 0 )
        {
            $updates_are_available = count($system_data["os_updates"]);
            $plural = $updates_are_available > 1;
          
            $i18n_main_msg = $plural ? "{} updates available" : "{} update available";

            $system_update_msg = "<div class=\"info\" data-i18n=\"" . $i18n_main_msg . "\" data-i18n_1=\"" . $updates_are_available . "\"></div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UNCore.actionInstallUpdates(this)\" data-i18n=\"Install\"></div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'systemUpdateDetails')\"></div></div>";

            $system_update_details = "<div class=\"row\">
                  <div data-i18n=\"Name\"></div>
                  <div data-i18n=\"Current\"></div>
                  <div class=\"grow\" data-i18n=\"Update\"></div>
                  <div data-i18n=\"Arch\"></div>
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
            $system_update_msg = "<div class=\"info\" data-i18n=\"No updates available\"></div>";
            $system_update_details = "";
        }
        
        return [ $updates_are_available, $system_update_msg, $system_update_details ];
    }
       
    public static function getDeploymentUpdate($system_data)
    {
        $updates_are_available = 0;
        if( isset($system_data["smartserver_changes"]) && count($system_data["smartserver_changes"]) > 0 )
        {
            $updates_are_available = count($system_data["smartserver_changes"]);
            $plural = $updates_are_available > 1;
          
            $i18n_main_msg = $plural ? "{} updates available" : "{} update available";

            $deployment_update_msg = "<div class=\"info\" data-i18n=\"" . $i18n_main_msg . "\" data-i18n_1=\"" . $updates_are_available . "\"></div><div class=\"buttons\"><div class=\"form button exclusive green\" onclick=\"mx.UNCore.actionDeployUpdates(this)\" data-i18n=\"Install\"></div><div class=\"form button toggle\" onclick=\"mx.UNCore.toggle(this,'deploymentUpdateDetails')\"></div></div>";

            $deployment_update_details_msg = "<div class=\"row\">
                  <div data-i18n=\"Flag\"></div>
                  <div class=\"grow\" data-i18n=\"File\"></div>
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
            $deployment_update_msg = "<div class=\"info\" data-i18n=\"No updates available\"></div>";
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
            $is_plural = $system_update_available + $deployment_update_available > 1;
            
          
            $types = [];
            if( $system_update_available ) $types[] = $system_update_available . " system update" . ( $system_update_available > 1 ? 's' : '' );
            if( $deployment_update_available ) $types[] = $deployment_update_available . " smartserver update" . ( $deployment_update_available > 1 ? 's' : '' );
            
            
            #implode(" and ",$types)
            
            if( $system_update_available > 0 && $deployment_update_available > 0 )
            {
                $msg = "There are {1} {2} and {3} {4} update(s) available";
            }
            else if( $system_update_available > 1 || $deployment_update_available > 1 ) 
            {
                $msg = "There are {1} {2} updates available";
            }
            else
            {
                $msg = "There is {1} {2} update available";
            }
            
            $workflow_msg = "<div class=\"info\"><span data-i18n=\"" . $msg . "\"";
            
            $index = 0;
            if( $system_update_available ) 
            {
                $workflow_msg .= " data-i18n_" . ($index+1) . "=\"" . $system_update_available . "\"";
                $workflow_msg .= " data-i18n_" . ($index+2) . "_key=\"system\"";
                $index = 2;
            }
            if( $deployment_update_available ) 
            {
                $workflow_msg .= " data-i18n_" . ($index+1) . "=\"" . $deployment_update_available . "\"";
                $workflow_msg .= " data-i18n_" . ($index+2) . "_key=\"smartserver\"";
            }
            
            $workflow_msg .= "></span>";
            
            $workflow_fallback_msg = $workflow_msg;
            $workflow_fallback_msg .= "<div class=\"sub\" data-i18n=\"Currently disabled because it is only possible max. 5 minutes after a system status refresh\"></div>";
            
            $_workflow_msg = "</div><div class=\"buttons\"><div class=\"form button exclusive";
            $workflow_msg .= $_workflow_msg;
            $workflow_fallback_msg .= $_workflow_msg;
            $workflow_fallback_msg .= " disabled blocked";
            
            $_workflow_msg = " green\" onclick=\"mx.UNCore.actionUpdateWorkflow(this)\" data-i18n=\"Install all\"></div></div>";
            $workflow_msg .= $_workflow_msg;
            $workflow_fallback_msg .= $_workflow_msg;

            if( $now->getTimestamp() - $last_update->getTimestamp() > $timeout )
            {
                $workflow_msg = $workflow_fallback_msg;
                $workflow_fallback_msg = "";
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
            $reboot_needed_msg = "<div class=\"info red\"><span data-i18n=\"Reboot needed\"></span>";
            $reasons = [];
            if( $system_data["os_reboot"] ) $reasons[] = "installed system updates";
            if( $needs_system_reboot ) $reasons[] = "outdated processes";

            $msg = $system_data["os_reboot"] && $needs_system_reboot ? "Is needed because of {1} and {2}" : "Is needed because of {}";

            $reboot_needed_msg .= "<div class=\"sub\" data-i18n=\"" . $msg . "\"";
            foreach( $reasons as $index => $reason )
            {
                $reboot_needed_msg .= " data-i18n_" . ( $index + 1) . "_key=\"" . $reason . "\"";
            } 
            $reboot_needed_msg .= "></div>";
            
            
            $reboot_needed_msg .= "</div><div class=\"buttons\"><div class=\"form button exclusive red\" onclick=\"mx.UNCore.actionRebootSystem(this)\" data-i18n=\"Reboot system\"></div></div>";
        }
        
        return [ $service_restarts, $reboot_needed_msg ];
    }
    
    public static function getDeploymentCheckState($system_data)
    {
        list(, $last_smartserver_pull_fmt, ) = IndexTemplate::extractDate($system_data, "smartserver_pull");
        $deployment_update_code = isset($system_data["smartserver_code"]) ? $system_data["smartserver_code"] : "";
        
        list($colorClass,$updateMsg) = IndexTemplate::$deploymentUpdateInfoCodes[$deployment_update_code];
        
        return "<div class=\"info " . $colorClass . "\"><span data-i18n=\"" . $updateMsg . "\"></span><div class=\"sub\" data-i18n=\"Last git pull was on {}\" data-i18n_1=\"" .$last_smartserver_pull_fmt . "\"></div></div>";
    }
    
    public static function dump($system_state_file,$deployment_state_file,$deployment_tags_file,$outdated_roles_state_file,$deployment_logs_folder,$forced_data)
    {
        #error_log(print_r($forced_data));
        #error_log(in_array("system_updates.state",$forced_data));
      
        $result = "<div id=\"data\" style=\"display:none\">";
        
        if( $forced_data == null or in_array("system_updates.state",$forced_data) or in_array("outdated_roles.state",$forced_data))
        {
            $system_data = IndexTemplate::getSystemData($system_state_file);   

            list($last_outdated_roles_state_state, $last_outdated_roles_state_state_fmt, $last_outdated_roles_state_timestamp) = IndexTemplate::extractFileDate($outdated_roles_state_file);
            
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
            
            $roles_data = IndexTemplate::getOutdatedRolesData($outdated_roles_state_file);
            
            list($system_state_msg,$system_state_details_msg, $role_state_msg, $role_state_details_msg ) = IndexTemplate::getSystemState($system_data, $service_restarts, $roles_data);
            $result .= "<div class=\"roleStateHeader\">" . $role_state_msg . "</div>";
            $result .= "<div class=\"roleStateDetails\">" . $role_state_details_msg . "</div>";
            $result .= "<div class=\"roleStateDateAsTimestamp\">" . $last_outdated_roles_state_timestamp . "</div>";
            $result .= "<div class=\"roleStateDateFormatted\">" . $last_system_state_fmt . "</div>";
            
            
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
