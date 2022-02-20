<?php
require "../shared/libs/logfile.php";
require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "inc/job.php";

require "config.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link href="<?php echo Ressources::getCSSPath('/update_service/'); ?>" rel="stylesheet">
<link rel="stylesheet" href="/shared/css/logfile/logfile_box.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/update_service/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/update_service/'); ?>"></script>
<script src="/shared/js/logfile/logfile.js"></script>
</head>
<body class="inline spacer system">
<script>
    mx.OnScriptReady.push( mx.Page.initBody );

    mx.UNCore = (function( ret ) {
        var job_is_running = null;
        var job_running_type = null;
        var job_cmd_type = null;
        var job_started = null;
        
        var systemUpdatesCount = 0;
        var smartserverChangeCount = 0;
        
        var hasEncryptedVault = false;
        
        var refreshDaemonStateTimer = 0;
        
        var deploymentTags = [];
        
        var workflowTimer = 0;
        
        var dialog = null;
        
        var daemonApiUrl = mx.Host.getBase() + '../api.php'; 
       
        function processData(last_data_modified, changed_data)
        {
            if( changed_data.hasOwnProperty("has_encrypted_vault") ) hasEncryptedVault = changed_data["has_encrypted_vault"];
            
            if( changed_data.hasOwnProperty("deployment_tags") ) deploymentTags = changed_data["deployment_tags"];
                 
            let updateBehaviorChanged = false;
            
            const [ lastUpdateDate, lastUpdateMsg ] = mx.UpdateServiceTemplates.getLastFullRefresh(last_data_modified);
            let lastUpdateDateElement = mx.$("#lastUpdateDateFormatted");
            if( lastUpdateMsg != lastUpdateDateElement.innerHTML ) 
            {
                lastUpdateDateElement.innerHTML = lastUpdateMsg;
                if( lastUpdateDate == null ) lastUpdateDateElement.classList.add("red");
                else lastUpdateDateElement.classList.remove("red");
                 
                updateBehaviorChanged = true
            }
            
            if( changed_data.hasOwnProperty("outdated_processes") || changed_data.hasOwnProperty("outdated_roles") )
            {
                const [ processDetails, processHeader, rolesDetails, rolesHeader, roleCount ] = mx.UpdateServiceTemplates.getSystemOutdatedDetails(last_data_modified, changed_data);
                
                mx.UpdateServiceHelper.setTableContent(processDetails,"systemStateDetails", processHeader, "systemStateHeader");
                
                mx.UpdateServiceHelper.setTableContent(rolesDetails,"roleStateDetails",rolesHeader,"roleStateHeader")
            }
            
            if( changed_data.hasOwnProperty("is_reboot_needed") )
            {
                const rebootNeededDetails = mx.UpdateServiceTemplates.getSystemStateDetails(last_data_modified, changed_data)
                
                let rebootNeededElement = mx.$("#systemRebootState");
                rebootNeededElement.innerHTML = rebootNeededDetails;
                rebootNeededElement.style.display = rebootNeededDetails ? "" : "None";
            }

            if( changed_data.hasOwnProperty("system_updates") )
            {
                const [ _systemUpdateCount, systemUpdateDetails, systemUpdateHeader ] = mx.UpdateServiceTemplates.getSystemUpdateDetails(last_data_modified, changed_data, lastUpdateDate);
                systemUpdatesCount = _systemUpdateCount
                updateBehaviorChanged = true;
                
                mx.UpdateServiceHelper.setTableContent(systemUpdateDetails,"systemUpdateDetails",systemUpdateHeader,"systemUpdateHeader")
            }
            
            if( changed_data.hasOwnProperty("smartserver_changes") )
            {
                const [ _smartserverChangeCount, smartserverChangeDetails, smartserverChangeHeader ] = mx.UpdateServiceTemplates.getSmartserverChangeDetails(last_data_modified, changed_data, lastUpdateDate);
                smartserverChangeCount = _smartserverChangeCount
                updateBehaviorChanged = true;

                mx.UpdateServiceHelper.setTableContent(smartserverChangeDetails,"smartserverChangeDetails",smartserverChangeHeader,"smartserverChangeHeader")
            }
            
            if( changed_data.hasOwnProperty("smartserver_code") )
            {
                const smartserverChangeState = mx.UpdateServiceTemplates.getSmartserverChangeState(last_data_modified, changed_data);
                let smartserverChangeStateElement = mx.$("#smartserverChangeState");
                smartserverChangeStateElement.style.display = smartserverChangeState ? "" : "None";
                smartserverChangeStateElement.innerHTML = smartserverChangeState;
            }
            
            if( changed_data.hasOwnProperty("jobs") )
            {
                const [ jobDetails, jobHeader ] = mx.UpdateServiceTemplates.getJobDetails(last_data_modified, changed_data);
                mx.UpdateServiceHelper.setTableContent(jobDetails,"lastRunningJobsDetails",jobHeader,"lastRunningJobsHeader");
            }

            if( updateBehaviorChanged )
            {
                function setWorkflowMessage()
                {
                    window.clearTimeout(workflowTimer);

                    const [updateWorkflowContent, timeout ] = mx.UpdateServiceTemplates.getWorkflow(systemUpdatesCount, smartserverChangeCount, lastUpdateDate);
                    
                    var updateWorkflowElement = mx.$("#updateWorkflow");
                    updateWorkflowElement.innerHTML = updateWorkflowContent;
                    updateWorkflowElement.style.display = updateWorkflowContent ? "" : "None";
                    
                    return timeout;
                }
                
                let timeout = setWorkflowMessage();
                if( timeout >= 0 )
                {
                    workflowTimer = window.setTimeout(setWorkflowMessage,timeout);
                }
            }
            
            if( Object.keys(changed_data).length > 0 ) mx.Page.refreshUI();
        }
        
        function handleDaemonState(state)
        {
            window.clearTimeout(refreshDaemonStateTimer);
           
            var daemonNeedsRestart = state["update_server_needs_restart"];
            var needsRestartElement = mx.$("#serverNeedsRestart");
            needsRestartElement.style.display = daemonNeedsRestart ? "flex" : "";
            
            job_is_running = state["job_is_running"];
            job_running_type = state["job_running_type"];
            job_cmd_type = state["job_cmd_type"];
            job_started = state["job_started"];
            
            var msg = "";
            var currentRunningStateElement = mx.$("#currentRunningState");
            var currentRunningActionsElement = mx.$("#currentRunningActions");
            if( job_is_running )
            {
                var logfile = state["job_logfile"];
                if( logfile && job_started)
                {
                    var logfile_name = logfile.substring(0,logfile.length - 4);
                    var data = logfile_name.split("-");

                    action_msg_1 = "<div class=\"detailView\" onClick=\"mx.UNCore.openDetails(this,'" + data[0] + "','" + data[3] + "','" + data[4] + "')\">";
                    action_msg_2 = "</div>";
                
                    var runtime = Math.round( ( (new Date()).getTime() - Date.parse(job_started) ) / 1000 );
                    
                    msg = mx.UpdateServiceTemplates.getActiveServiceJobName(job_cmd_type).fill({"1": action_msg_1, "2": action_msg_2, "3": runtime, "4": mx.I18N.get( runtime == 1 ? "second" : "seconds" ) });
                    
                    if( state["job_killable"] )
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
                    msg = mx.UpdateServiceTemplates.getActiveManuellJobName(job_cmd_type);
                    currentRunningActionsElement.style.display= ""
                }
                
                currentRunningStateElement.innerHTML = msg;
                
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 1000);
            }
            else
            {
                currentRunningActionsElement.style.display="";
                currentRunningActionsElement.querySelector(".button").classList.remove("disabled");

                currentRunningStateElement.innerHTML = mx.I18N.get("No update process is running");

                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
            }
           
            if( Object.keys(state["changed_data"]).length > 0 ) processData(state["last_data_modified"], state["changed_data"]);
                 
            if( dialog != null && dialog.getId() != "killProcess" ) 
            { 
                if( job_is_running )
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
            
            if( job_is_running )
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
        
        function refreshDaemonState(last_data_modified,callback)
        {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", daemonApiUrl);
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    var response = JSON.parse(this.response);
                    if( response["status"] == "0" )
                    {
                        mx.UpdateServiceHelper.confirmSuccess();
                        
                        handleDaemonState(response);
                        
                        if( callback ) callback();
                    }
                    else
                    {
                        mx.UpdateServiceHelper.handleServerError(response["message"])
                    }
                }
                else if( this.status == 503 ) 
                {
                    mx.UpdateServiceHelper.handleServerNotAvailable();
                    refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(last_data_modified, callback) }, mx.UpdateServiceHelper.isRestarting() ? 1000 : 15000 );
                }
                else
                {
                    if( this.status != 0 && this.status != 401 ) mx.UpdateServiceHelper.handleRequestError(this.status, this.statusText, this.response);
                    refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(last_data_modified, callback) }, 15000);
                }
            };
            
            xhr.send(JSON.stringify({"action": "state", "parameter": { "type": "update", "last_data_modified": last_data_modified }}));
        }
        
        function runAction(btn, action, parameter, response_callback)
        {
            // needs to be asynchrone to allow ripple effect
            window.setTimeout(function() { btn.classList.add("disabled"); },0);
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", daemonApiUrl );
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( response_callback )
                {
                    response_callback(this);
                }
                else
                {
                    if( this.status == 200 ) 
                    {
                        var response = JSON.parse(this.response);
                        if( response["status"] == "0" )
                        {
                            mx.UpdateServiceHelper.confirmSuccess();

                            handleDaemonState(response);
                        }
                        else
                        {
                            mx.UpdateServiceHelper.handleServerError(response["message"]);
                        }
                    }
                    else if( this.status == 503 ) 
                    {
                        mx.UpdateServiceHelper.handleServerNotAvailable();
                    }
                    else
                    {
                        mx.UpdateServiceHelper.handleRequestError(this.status, this.statusText, this.response);
                    }
                }
            };
            xhr.send(JSON.stringify({"action": action, "parameter": parameter }));
        }
        
        function dialogClose()
        {
            dialog.close(); 
            dialog = null;
        }
        
        function confirmAction(btn, action, parameter, confirm, button_color, response_callback, confirmed_callback )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            if( confirm )
            {
                let cls = [ "continue" ];
                if( button_color ) cls.push(button_color);
                dialog = mx.Dialog.init({
                    id: action,
                    title: mx.I18N.get("Are you sure?"),
                    body: confirm,
                    buttons: [
                        { "text": mx.I18N.get("Continue"), "class": cls, "callback": function(){ dialogClose(); if( confirmed_callback ){ confirmed_callback(); } runAction(btn, action, parameter, response_callback); } },
                        { "text": mx.I18N.get("Cancel"), "callback": dialogClose },
                    ],
                    class: "confirmDialog",
                    destroy: true
                });
                dialog.open();
                mx.Page.refreshUI(dialog.getRootElement());
            }
            else
            {
                runAction(btn, action, parameter);
            }
        }

        ret.openDetails = function(event,datetime,cmd,username)
        {
            document.location = '../details/?datetime=' + datetime + '&cmd=' + cmd + '&username=' + username;
        }

        function updateDialog(type, btn, args, callback )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            var has_tags = args != null && args.hasOwnProperty("tags");
            
            var passwordField = null;
            var passwordRemember = null;
            var passwordHint = null;
            var tagHint= null;
            var confirmField = null;

            var body = "";
            if( type == "deployment" )
            {
                if( has_tags )
                {
                    var msg = args["tags"].indexOf(',') != -1 ? mx.I18N.get('all outdated roles') : args["tags"];
                    body += mx.I18N.get("You want to <span class='important'>redeploy '{}'</span>?").fill(msg);            
                }
                else
                {
                    body += mx.I18N.get("You want to <span class='important'>deploy smartserver updates</span>?");            
                }
            }
            else
            {
                body += mx.I18N.get("You want to <span class='important'>update everything</span>?<span class='spacer'></span>This includes <span class='important'>a system restart</span>, if necessary.");            
            }
            
            let hasPasswordField = hasEncryptedVault;
            let hasTagField = type == "deployment" && !has_tags;
            
            if( hasPasswordField || hasTagField )
            {
                body += "<br><br><div class=\"form table\">";
                
                if( hasEncryptedVault )
                {
                    var lastDeploymentPassword = sessionStorage.getItem("lastDeploymentPassword");
                    
                    body += "<div class=\"row\">";
                    body += "  <div>" + mx.I18N.get("Password") + ":</div>";
                    body += "  <div>";
                    body += "    <input name=\"password\" type=\"password\" autocomplete=\"on\"";
                    if( lastDeploymentPassword ) body += " value=\"" + lastDeploymentPassword + "\"";
                    body += "    >";
                    body += "    <div class=\"middle\"><input type=\"checkbox\" id=\"remember\" name=\"remember\"";
                    if( lastDeploymentPassword ) body += " checked";
                    body += ">";
                    body += "    <label for=\"remember\">" + mx.I18N.get("Remember") + "</label>";
                    body += "   </div>";
                    body += "   <div class=\"password hint red\">" + mx.I18N.get("Please enter a password") + "</div>";
                    body += "  </div>";
                    body += "</div>";
                }
                
                if( hasTagField )
                {
                    body += "<div class=\"row\">";
                    body += "  <div>" + mx.I18N.get("Tags") + ":</div>";
                    body += "  <div>";
                    body += "    <input name=\"tag\" autocomplete=\"off\"><div class=\"tag hint red\">" + mx.I18N.get("Please select a tag. e.g 'all'") + "</div>";
                    body += "  </div>";
                    body += "</div>";
                    body += "<div class=\"row\">";
                    body += "  <div>&nbsp;</div>";
                    body += "  <div>&nbsp;</div>";
                    body += "</div>";
                    
                    body += "</div>"; // => table close
                    
                    body += "<div class=\"deployConfirmation middle\">";
                    body += "  <input type=\"checkbox\" id=\"confirm\" name=\"confirm\" checked><label for=\"confirm\">" + mx.I18N.get("Mark all changes as deployed") + "</label>";
                    body += "</div>";
                }
                else
                {
                    body += "</div>"; // => table close
                }
            }
                
            var autocomplete = null;
            dialog = mx.Dialog.init({
                title: mx.I18N.get("Are you sure?"),
                body: body,
                buttons: [
                    { "text": mx.I18N.get("Continue"), "class": [ "continue", "green" ], "callback": function(){ 
                        let hasErrors = false;
                        
                        parameter = {};
                        if( hasPasswordField )
                        {
                            if( !passwordField.value )
                            {
                                passwordHint.style.maxHeight = passwordHint.scrollHeight + 'px';
                                hasErrors = true;
                            }
                            else
                            {
                                passwordHint.style.maxHeight = "";
                                parameter["password"] = passwordField.value;
                                if( passwordRemember.checked ) sessionStorage.setItem("lastDeploymentPassword", passwordField.value);
                                else sessionStorage.removeItem("lastDeploymentPassword");
                            }
                        }
                        
                        if( type == "deployment" )
                        {
                            if( hasTagField )
                            {
                                var selectedTags = autocomplete.getSelectedValues();
                                autocomplete.setTopValues(selectedTags);
                                var selectedTagsAsString = selectedTags.join(",");
                                
                                if( selectedTags.length == 0 && !confirmField.checked)
                                {
                                    tagHint.style.maxHeight = tagHint.scrollHeight + 'px';
                                    hasErrors = true;
                                }
                                else
                                {
                                    tagHint.style.maxHeight = "";
                                    localStorage.setItem("lastSelectedDeploymentTags", selectedTagsAsString);
                                    parameter["tags"] = selectedTagsAsString;
                                    parameter["confirm"] = confirmField.checked;
                                }
                            }
                            else
                            {
                                parameter["tags"] = args["tags"]
                                parameter["confirm"] = false;
                            }
                        }

                        if( !hasErrors )
                        {
                            dialog.close(); 
                            
                            callback(parameter);
                        }
                    } },
                    { "text": mx.I18N.get("Cancel"), "callback": dialogClose },
                ],
                class: "confirmDialog",
                destroy: true
            });
            dialog.open();
            mx.Page.refreshUI(dialog.getRootElement());
            
            if( hasPasswordField )
            {
                passwordField = dialog.getElement("input[name=\"password\"]");
                passwordRemember = dialog.getElement("input[name=\"remember\"]");
                passwordHint = dialog.getElement(".password.hint");
            }
            
            if( hasTagField )
            {
                tagHint = dialog.getElement(".tag.hint");
                confirmField = dialog.getElement("input[name=\"confirm\"]");    

                var lastSelectedTags = localStorage.getItem("lastSelectedDeploymentTags");
                
                autocomplete = mx.Autocomplete.init({
                    values: deploymentTags,
                    top_values: lastSelectedTags ? lastSelectedTags.split(",") : [],
                    selected_values: [ "all" ],
                    selectors: {
                        input: "input[name=\"tag\"]"
                    }
                });
                dialog.addEventListener("destroy",autocomplete.destroy);
                
                confirmField.disabled = true;
                
                let lastIncludesAll = true;
                function selectionHandler(event)
                {
                    let values = autocomplete.getSelectedValues();
                    values = [...values];
                    
                    if( values.includes("all") )
                    {
                        if( values.length > 1 )
                        {
                            if( event["detail"]["added"] && event["detail"]["value"] == "all" )
                            {
                                for( let i = 0; i < values.length; i++ )
                                {
                                    let value = values[i];
                                    if( value != "all" )
                                    {
                                        autocomplete.removeValueFromSelection(value);
                                        console.log(value);
                                    }
                                }
                                confirmField.checked = true;
                                confirmField.disabled = true;
                            }
                            else
                            {
                                autocomplete.removeValueFromSelection("all");
                                confirmField.checked = false;
                                confirmField.disabled = false;
                            }
                        }
                        else
                        {
                            confirmField.checked = true;
                            confirmField.disabled = true;
                        }
                    }
                    else
                    {
                        confirmField.disabled = false;
                    }
                    //if( autocomplete.getSelectedValues().length>0 ) confirmField.checked = false;
                    //else confirmField.checked = true;
                 
                }
                autocomplete.getRootLayer().addEventListener("selectionChanged",selectionHandler);
            }
        }
        
        ret.actionDeployUpdates = function(btn)
        {
            var tag = btn.dataset.tag;
            parameter = tag ? { "tags": tag } : null;
            updateDialog("deployment",btn,parameter,function(parameter){
                runAction(btn, 'deploySmartserverUpdates', parameter); 
            });
        }
        
        ret.actionUpdateWorkflow = function(btn)
        {
            updateDialog("all",btn,null,function(parameter){
                runAction(btn, 'updateWorkflow', parameter); 
            });
        }
        
        ret.actionRebootSystem = function(btn)
        {
            confirmAction(btn,'systemReboot',null,mx.I18N.get("You want to <span class='important'>reboot your system</span>?"),"red");          
        }
        
        ret.actionRestartServices = function(btn)
        {
            var service = btn.dataset.service;
            var msg = service.indexOf(',') != -1 ? mx.I18N.get("all outdated services") : service;
            confirmAction(btn,'restartService',{'service': service}, mx.I18N.get("You want to <span class='important'>restart '{}'</span>?").fill(msg),"yellow");
        }
        
        ret.actionInstallUpdates = function(btn)
        { 
            confirmAction(btn,'installSystemUpdates',null,mx.I18N.get("You want to <span class='important'>install system updates</span>?"),"green");          
        }
        
        ret.actionRefreshUpdateState = function(btn,type)
        { 
            confirmAction(btn,'refreshSystemUpdateCheck', { "type": type });
        }

        ret.actionKillProcess = function(btn)
        {
            confirmAction(btn,'killProcess',null,mx.I18N.get("You want to kill current running job?"),"red");
        }

        ret.actionRestartDaemon = function(btn)
        {
            confirmAction(btn,'restartDaemon',null,mx.I18N.get("You want to <span class='important'>restart update daemon</span>?"),"red",null, mx.UpdateServiceHelper.announceRestart );
            /*, function(response){
            window.clearTimeout(refreshDaemonStateTimer);
            confirmAction(btn,'restartDaemon',null,mx.I18N.get("You want to <span class='important'>restart update daemon</span>?"),"red", function(response){
                mx.UpdateServiceHelper.setExclusiveButtonsState(false,null)
                window.setTimeout(function(){ refreshDaemonState(null); },2000);
            });*/
        }
        
        ret.toggle = function(btn,id)
        {
            var element = mx.$("#"+id);
            if( element.style.maxHeight )
            {
                element.style.maxHeight = "";
                window.setTimeout(function(){ element.style.display=""; mx.UpdateServiceHelper.setToogle(btn,element); },300);
            }
            else
            {
                element.style.display = "block";
                window.setTimeout(function(){ 
                    mx.UpdateServiceHelper.setScrollHeight(element);
                    mx.UpdateServiceHelper.setToogle(btn,element); 
                },0);
            }
        }

        ret.init = function()
        { 
            mx.I18N.process(document);
            
            mx.Selectbutton.init({
                values: [
                    { "text": mx.I18N.get("Only smartserver updates"), "onclick": function(){ mx.UNCore.actionRefreshUpdateState(this,'deployment_update') } },
                    { "text": mx.I18N.get("Only system updates"), "onclick": function(){ mx.UNCore.actionRefreshUpdateState(this,'system_update') } },
                    { "text": mx.I18N.get("Only outdated processes"), "onclick": function(){ mx.UNCore.actionRefreshUpdateState(this,'process_update') } }
                ],
                selectors: {
                    button: "#searchUpdates"
                }
            });
          
            refreshDaemonState(null, function(){
                window.setTimeout(function(){
                    var initialLists = ["systemProcesses","smartserverRoles"];
                    initialLists.forEach(function(id){
                        var element = mx.$("#" + id);
                        if( element ) element.click();
                    });
                },100);
            });

            mx.Page.init(mx.I18N.get("Updates"));            
        }
        return ret;
    })( mx.UNCore || {} );
    
    mx.OnDocReady.push( mx.UNCore.init );
</script>
<div class="widget summery">
    <div class="action" id="updateWorkflow"></div>
    <div class="action"><div class="info" id="lastUpdateDateFormatted"></div><div class="buttons"><div class="form button exclusive" id="searchUpdates" onclick="mx.UNCore.actionRefreshUpdateState(this)" data-i18n="Check for updates"></div></div></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Status"></div></div>

    <div class="action" id="serverNeedsRestart"><div class="info red" data-i18n="Daemon was updated and needs to restart"></div><div class="buttons"><div class="form button restart red exclusive" onclick="mx.UNCore.actionRestartDaemon(this)" data-i18n="Restart daemon"></div></div></div>
    
    <div class="action"><div class="info" id="currentRunningState"></div><div class="buttons" id="currentRunningActions"><div class="form button kill red" onclick="mx.UNCore.actionKillProcess(this)" data-i18n="Stop"></div></div></div>
    <div class="action" id="lastRunningJobsHeader"></div>
    <div class="list form table logfileBox" id="lastRunningJobsDetails"></div>

    <div class="action" id="systemRebootState"></div>
    
    <div class="action" id="systemStateHeader"></div>
    <div class="list form table" id="systemStateDetails"></div>
    
    <div class="action" id="roleStateHeader"></div>
    <div class="list form table" id="roleStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Details"></div></div>
   
    <div class="action" id="systemUpdateHeader"></div>
    <div class="list form table" id="systemUpdateDetails"></div>

    <div class="action" id="smartserverChangeHeader"></div>
    <div class="list form table" id="smartserverChangeDetails"></div>
    <div class="action" id="smartserverChangeState"></div>
</div>
<div class="error"></div>
</body>
</html>
