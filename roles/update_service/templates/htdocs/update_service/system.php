<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/shared/mod/logfile/","/update_service/"]); ?>
<script>
mx.UNCore = (function( ret ) {
    var updateJobStarted = false;

    var systemUpdatesCount = 0;
    var smartserverChangesCount = 0;
    var systemUpdatesHash = "";
    var smartserverChangesHash = "";

    var last_data_modified = null;
    var hasEncryptedVault = false;
    var deploymentTags = [];

    var daemonNeedsRestart = false;
    var job_state = {};
    var workflow_status = null;
    var last_refreshed_state = {};
    var workflow_timer = null;
    var last_msg = null;

    var job_runtime_ref = null;
    var job_runtime_timer = null;
    var job_runtime_started = null;

    function calculateRuntime()
    {
        let runtime = Math.round( ( (new Date()).getTime() - job_runtime_started ) / 1000 );
        if( runtime == 0 ) return mx.I18N.get("is started");
        return mx.I18N.get("is running since {1}").fill({"1": runtime + " " + mx.I18N.get( runtime == 1 ? "second" : "seconds" ) });
    }

    function runtimeRefresh()
    {
        mx.$("#runtime_duration_placeholder").innerText = calculateRuntime();

        if( job_runtime_timer != null )
        {
            let now = window.performance.now();
            let duration = now - job_runtime_ref;
            let sleep = 2000 - duration;
            if( sleep < 0 ) sleep = 1000 - ( ( sleep % 1000 ) * -1 );
            job_runtime_ref = now;
            job_runtime_timer = window.setTimeout(runtimeRefresh, sleep );
        }
    }

    function stopRuntimeTimer()
    {
        if( job_runtime_timer != null )
        {
            window.clearTimeout(job_runtime_timer);
            job_runtime_timer = null;
        }
    }

    function processRunningJobDetails(data)
    {
        if( "job_status" in data ) job_state = {...job_state, ...data["job_status"]};

        if( "workflow_status" in data ) workflow_status = data["workflow_status"];

        let job_is_running = job_state["job"] != null;
        let job_running_type = job_state["type"];
        let job_cmd_type = job_state["job"];
        let job_started = job_state["started"];

        var msg = "";
        var currentRunningStateElement = mx.$("#currentRunningState");
        var currentRunningActionsElement = mx.$("#currentRunningActions");

        if( workflow_timer != null )
        {
            window.clearTimeout(workflow_timer);
            workflow_timer = null;
        }

        if( job_is_running )
        {
            var logfile = job_state["logfile"];
            if( logfile && job_started )
            {
                let logfile_name = logfile.substring(0,logfile.length - 4);
                let logfile_parts = logfile_name.split("-");

                action_msg_1 = "<span class=\"detailView\" onClick=\"mx.UpdateServiceActions.openDetails(this,'" + logfile_parts[0] + "','" + logfile_parts[3] + "','" + logfile_parts[4] + "')\">";
                action_msg_2 = "</span>";

                job_runtime_started = Date.parse(job_started);

                msg = mx.UpdateServiceTemplates.getActiveServiceJobName(job_cmd_type);

                if( last_msg != msg )
                {
                    last_msg = msg;

                    currentRunningStateElement.innerHTML = msg.fill({"1": action_msg_1, "2": action_msg_2, "3": "<span id='runtime_duration_placeholder'>" + calculateRuntime() + "</span>"});

                    stopRuntimeTimer();
                    job_runtime_ref = window.performance.now();
                    job_runtime_timer = window.setTimeout(runtimeRefresh,1000);
                }

                if( job_state["killable"] )
                {
                    currentRunningActionsElement.style.display= "block";
                }
                else
                {
                    currentRunningActionsElement.style.display= "";
                    currentRunningActionsElement.querySelector(".button").classList.remove("disabled");
                }
            }
            else
            {
                stopRuntimeTimer();

                currentRunningActionsElement.style.display= ""

                msg = "<span class=\"icon-attention yellow\"></span> " + mx.UpdateServiceTemplates.getActiveManuellJobName(job_cmd_type);
                if( last_msg != msg )  currentRunningStateElement.innerHTML = last_msg = msg;
            }
        }
        else if( workflow_status == "running" || workflow_status == "waiting" )
        {
            // delay waiting workflow_status, to give follow up job a chance to start
            workflow_timer = window.setTimeout(function()
            {
                workflow_timer = null;

                stopRuntimeTimer();

                currentRunningActionsElement.style.display= "block";
                currentRunningStateElement.innerHTML = "<span class=\"icon-attention yellow\"></span> " + mx.I18N.get("Process is still ongoing and will continue soon");;
            }, 1000);
        }
        else
        {
            stopRuntimeTimer();

            currentRunningActionsElement.style.display="";
            currentRunningActionsElement.querySelector(".button").classList.remove("disabled");

            if( workflow_status == "done" )
            {
                msg = mx.I18N.get("No update process is running");
            }
            else
            {
                switch (workflow_status) {
                    case 'killed':
                        msg = mx.I18N.get("Last process was killed")
                        break;
                    case 'stopped':
                        msg = mx.I18N.get("Last process was stopped")
                        break;
                    default:
                        let reasons = workflow_status.split(",");
                        if( reasons.indexOf("wrong_system_update_hash") != -1 && reasons.indexOf("wrong_smartserver_update_hash") != -1 )
                        {
                            msg = mx.I18N.get("Last process was stopped, because of new system and smartserver updates");
                        }
                        else if( reasons.indexOf("wrong_system_update_hash") != -1 )
                        {
                            msg = mx.I18N.get("Last process was stopped, because of new system updates");
                        }
                        else if( reasons.indexOf("wrong_smartserver_update_hash") != -1 )
                        {
                            msg = mx.I18N.get("Last process was stopped, because of new smartserver updates");
                        }
                        break;
                }

                msg = "<span class=\"icon-attention red\"></span> " + msg;
            }
            if( last_msg != msg )  currentRunningStateElement.innerHTML = last_msg = msg;
        }

        if( mx.UpdateServiceActions.getDialog() != null )
        {
            let dialog = mx.UpdateServiceActions.getDialog();
            if( dialog.getId() != "killProcess" )
            {
                if( workflow_status == "running" || workflow_status == "waiting" )
                {
                    let msg = mx.I18N.get("'{}' disabled, because of a running job");
                    msg = msg.fill(dialog.getElement(".continue").innerHTML);
                    dialog.setInfo(msg);
                    dialog.setActionDisabled(".continue",true);
                }
                else
                {
                    dialog.setInfo("");
                    dialog.setActionDisabled(".continue",false);
                }
            }
        }

        if( workflow_status == "running" || workflow_status == "waiting" || job_is_running )
        {
            mx.UpdateServiceHelper.setExclusiveButtonsState(false, job_running_type == "manual" ? null: "kill");
        }
        else
        {
            if( daemonNeedsRestart )
            {
                mx.UpdateServiceHelper.setExclusiveButtonsState(false, "restart");
            }
            else
            {
                mx.UpdateServiceHelper.setExclusiveButtonsState(true, null );
            }
        }
    }

    ret.processData = function(data)
    {
        if( data["has_encrypted_vault"] ) hasEncryptedVault = data["has_encrypted_vault"];

        if( data["deployment_tags"] ) deploymentTags = data["deployment_tags"];

        let updateBehaviorChanged = false;

        if( "update_server_needs_restart" in data )
        {
            daemonNeedsRestart = data["update_server_needs_restart"];
            var needsRestartElement = mx.$("#serverNeedsRestart");
            needsRestartElement.style.display = daemonNeedsRestart ? "flex" : "";
        }

        if( data["outdated_roles"] || data["outdated_processes"] ) mx.UpdateServiceTemplates.setSystemOutdatedDetails( data["outdated_roles"], data["outdated_processes"], "#systemStateHeader", "#systemStateDetails", "#roleStateHeader", "#roleStateDetails" );

        if( data["is_reboot_needed"] ) mx.UpdateServiceTemplates.setSystemStateDetails(data["is_reboot_needed"],"#systemRebootState");

        if( data["smartserver_pull"] ) mx.UpdateServiceTemplates.setSmartserverChangeState(data["smartserver_pull"], "#smartserverChangeState");

        if( data["jobs"] ) mx.UpdateServiceTemplates.setJobDetails(data["jobs"], "#lastRunningJobsHeader", "#lastRunningJobsDetails");

        if( data["system_updates"] )
        {
            systemUpdatesCount = mx.UpdateServiceTemplates.setSystemUpdateDetails(data["system_updates"], "#systemUpdateHeader", "#systemUpdateDetails");
            updateBehaviorChanged = true;
        }

        if( data["smartserver_changes"] )
        {
            smartserverChangesCount = mx.UpdateServiceTemplates.setSmartserverChangeDetails(data["smartserver_changes"], "#smartserverChangeHeader", "#smartserverChangeDetails");
            updateBehaviorChanged = true;
        }

        if( data["last_refreshed"] ) last_refreshed_state = {...last_refreshed_state, ...data["last_refreshed"] };

        const [ lastUpdateDate, lastUpdateMsg ] = mx.UpdateServiceTemplates.getLastFullRefresh(last_refreshed_state);
        let lastUpdateDateElement = mx.$("#lastUpdateDateFormatted");
        if( lastUpdateMsg != lastUpdateDateElement.innerHTML )
        {
            lastUpdateDateElement.innerHTML = lastUpdateMsg;
            if( lastUpdateDate == null ) lastUpdateDateElement.classList.add("red");
            else lastUpdateDateElement.classList.remove("red");

            updateBehaviorChanged = true
        }

        if( updateBehaviorChanged ) mx.UpdateServiceTemplates.setWorkflow(systemUpdatesCount, smartserverChangesCount, "#updateWorkflow");

        let systemUpdatesHashChanged = false;
        let smartserverChangesHashChanged = false;
        let updateHashRefreshed = false;
        if( data["system_updates_hash"] )
        {
            updateHashRefreshed = true;
            if( systemUpdatesHash != data["system_updates_hash"] ) systemUpdatesHashChanged = true;
            systemUpdatesHash = data["system_updates_hash"];
        }
        if( data["smartserver_changes_hash"] )
        {
            updateHashRefreshed = true;
            if( smartserverChangesHash != data["smartserver_changes_hash"] ) smartserverChangesHashChanged = true;
            smartserverChangesHash = data["smartserver_changes_hash"];
        }

        if( updateJobStarted && updateHashRefreshed )
        {
            updateJobStarted = false;
            if( systemUpdatesHashChanged || smartserverChangesHashChanged )
            {
                let body = "";
                if( systemUpdatesHashChanged && smartserverChangesHashChanged ) body += mx.I18N.get("There are new system and smartserver update available!");
                else if( systemUpdatesHashChanged ) body += mx.I18N.get("There are new system update available!");
                else if( smartserverChangesHashChanged ) body += mx.I18N.get("There are new smartserver update available!");

                let infoDialog = mx.Dialog.init({
                    id: "stoppedUpdate",
                    title: mx.I18N.get("Installation stopped!"),
                    body: body + "<span class='spacer'></span>" + mx.I18N.get("Please check whether you want to install these updates and restart the installation process if necessary."),
                    buttons: [
                        { "text": mx.I18N.get("Ok") },
                    ],
                    class: "confirmDialog",
                    destroy: true
                });
                infoDialog.open();
                mx.Page.refreshUI(infoDialog.getRootElement());
            }
        }

        processRunningJobDetails(data);

        if( Object.keys(data).length > 0 ) mx.Page.refreshUI();
    }

    ret.setUpdateJobStarted = function( _updateJobStarted ){ updateJobStarted = _updateJobStarted; }

    ret.hasEncryptedVault = function(){ return hasEncryptedVault; }

    ret.getDeploymentTags = function(){ return deploymentTags; }

    ret.getLastDataModified = function(){ return last_data_modified; }

    ret.getSystemUpdatesCount = function(){ return systemUpdatesCount; }

    ret.getSmartserverChangesCount = function(){ return smartserverChangesCount; }

    ret.getLastDataModified = function(){ return last_data_modified; }

    ret.getUpdateHashes = function(){ return { "system_updates_hash": systemUpdatesHash, "smartserver_changes_hash": smartserverChangesHash }; }

    ret.handleDaemonState = function(state){ console.log(state); }

    ret.init = function()
    {
        mx.I18N.process(document);

        mx.Selectbutton.init({
            values: [
                { "text": mx.I18N.get("Only smartserver updates"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'deployment_update') } },
                { "text": mx.I18N.get("Only system updates"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'system_update') } },
                { "text": mx.I18N.get("Only outdated processes"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'process_update') } }
            ],
            selectors: {
                button: "#searchUpdates"
            }
        });
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );

var processData = mx.OnDocReadyWrapper( mx.UNCore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    let socket = mx.ServiceSocket.init('update_service','updates');
    socket.on("data", (data) => processData( data ) );
    mx.OnUpdateServiceReady.push(function(){ mx.UpdateServiceActions.init(socket); });
});
</script>
</head>
<body class="system">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer", mx.I18N.get("Update")); } );</script>
<div class="widget summery">
    <div class="action" id="updateWorkflow"></div>
    <div class="action"><div class="info" id="lastUpdateDateFormatted"></div><div class="buttons"><div class="form button exclusive" id="searchUpdates" onclick="mx.UpdateServiceActions.actionRefreshUpdateState(this)" data-i18n="Check for updates"></div></div></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Status"></div></div>

    <div class="action" id="serverNeedsRestart"><div class="info"><span class="icon-attention red"></span> <span data-i18n="Daemon was updated and needs to restart"></span></div><div class="buttons"><div class="form button restart red exclusive" onclick="mx.UpdateServiceActions.actionRestartDaemon(this)" data-i18n="Restart daemon"></div></div></div>
    
    <div class="action"><div class="info" id="currentRunningState"></div><div class="buttons" id="currentRunningActions"><div class="form button kill red" onclick="mx.UpdateServiceActions.actionKillProcess(this)" data-i18n="Stop"></div></div></div>
    <div class="action" id="lastRunningJobsHeader"></div>
    <div id="lastRunningJobsDetails"></div>

    <div class="action" id="systemRebootState"></div>
    
    <div class="action" id="systemStateHeader"></div>
    <div id="systemStateDetails"></div>
    
    <div class="action" id="roleStateHeader"></div>
    <div id="roleStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Details"></div></div>
   
    <div class="action" id="systemUpdateHeader"></div>
    <div id="systemUpdateDetails"></div>

    <div class="action" id="smartserverChangeHeader"></div>
    <div id="smartserverChangeDetails"></div>
    <div class="action" id="smartserverChangeState"></div>
</div>
</body>
</html>
