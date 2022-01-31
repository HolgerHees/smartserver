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
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
<link rel="stylesheet" href="/shared/css/logfile_box.css">
<link rel="stylesheet" href="./css/index.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
</head>
<body class="inline">
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
    
    mx.UNCore = (function( ret ) {
        var job_is_running = null;
        var job_running_type = null;
        var job_cmd_name = null;
        var job_started = null;
        
        var last_data_modified = null;

        var last_system_state_modified = null;
        var last_system_update_modified = null;
        var last_deployment_update_modified = null;
        
        var hasEncryptedVault = false;
        
        var refreshDaemonStateTimer = 0;
        
        var deploymentTags = [];
        
        var workflowTimer = 0;
        
        var daemonApiUrl = mx.Host.getBase() + 'api.php';
       
        function handleServerError( response )
        {
            alert(response["message"]);
        }
        
        function handleRequestError( code, text )
        {
            alert("error '" + code + " " + text + "'");
        }
        
        function setToogle(btnElement,detailElement)
        {
            if( btnElement != null ) btnElement.innerText = detailElement.style.maxHeight ? "Hide" : "Show";
        }

        function setScrollHeight(detailElement)
        {
            var limitHeight =  Math.round(window.innerHeight * 0.8);
            var maxHeight = ( detailElement.scrollHeight + 20 );
            if( maxHeight > limitHeight )
            {
                maxHeight = limitHeight;
                detailElement.style.overflowY = "scroll";
            }
            else
            {
                detailElement.style.overflowY = "";
            }
            detailElement.style.maxHeight = maxHeight + "px"; 
        }

        function fixScrollHeight(detailElement)
        {
            if( detailElement.style.maxHeight )
            {
                if( detailElement.innerHTML )
                {
                    setScrollHeight(detailElement)
                }
                else
                {
                    detailElement.style.maxHeight = "";
                    detailElement.style.display = "";
                }
            }
        }
        
        function setExclusiveButtonsState(flag)
        {
            if( flag )
            {
                mx.$$("div.form.button.exclusive:not(.blocked)").forEach(function(element){ element.classList.remove("disabled"); });
            }
            else
            {
                mx.$$("div.form.button.exclusive:not(.blocked)").forEach(function(element){ element.classList.add("disabled"); });
            }
        }

        function getContentValue(content,id)
        {
            return content.querySelector("." + id).innerHTML;
        }
        
        function setTableContent(content,tableId,headerId)
        {
            mx.$("#" + headerId).innerHTML = getContentValue(content, headerId);
                      
            var systemStateDetailsElement = mx.$("#" + tableId);
            systemStateDetailsElement.innerHTML = getContentValue(content, tableId)
            setToogle(mx.$("#" + headerId + " .form.button.toggle"),systemStateDetailsElement);
            fixScrollHeight(systemStateDetailsElement);
        }

        function setLastCheckedContent(content,id)
        {
            var element = mx.$("#" + id);
            var last = getContentValue(content, id);
            if( last ) element.innerHTML = "(checked on " + last + ")";
            else element.innerHTML = "(never checked)";
        }
        
        function processData(new_data,content)
        {
            if( !content) return;
                 
            if( new_data == null || new_data.indexOf("deployment.state") != -1 )
            {
                hasEncryptedVault = getContentValue(content,"hasEncryptedVault") == '1' ? true : false;
            }
            
            if( new_data == null || new_data.indexOf("job.state") != -1 )
            {
                setTableContent(content,"lastRunningJobsDetails","lastRunningJobsHeader");
            }
            
            if( new_data == null || new_data.indexOf("deployment.tags") != -1 )
            {
                deploymentTags = getContentValue(content,"deploymentTags").split(",");
            }

            if( new_data == null || new_data.indexOf("system_updates.state") != -1 )
            {
                mx.$("#lastUpdateDateFormatted").innerHTML = "Last full refresh on " + getContentValue(content,"lastUpdateDateFormatted");
                
                _last_system_state_modified = getContentValue(content,"systemStateDateAsTimestamp");
                if( last_system_state_modified == null || last_system_state_modified != _last_system_state_modified )
                {
                    last_system_state_modified = _last_system_state_modified;
                
                    setTableContent(content,"systemStateDetails","systemStateHeader")
                    setLastCheckedContent(content,"systemStateDateFormatted");

                    var rebootNeededElement = mx.$("#systemRebootState");
                    var rebootNeededContent = getContentValue(content,"systemRebootState");
                    rebootNeededElement.innerHTML = rebootNeededContent;
                    rebootNeededElement.style.display = rebootNeededContent ? "" : "None";
                }
                
                _last_system_update_modified = getContentValue(content,"systemUpdateDateAsTimestamp");
                if( last_system_update_modified == null || last_system_update_modified != _last_system_update_modified )
                {
                    last_system_update_modified = _last_system_update_modified;
                    
                    setTableContent(content,"systemUpdateDetails","systemUpdateHeader")
                    setLastCheckedContent(content,"systemUpdateDateFormatted");
                }

                _last_deployment_update_modified = getContentValue(content,"deploymentUpdateDateAsTimestamp");
                if( last_deployment_update_modified == null || last_deployment_update_modified != _last_deployment_update_modified )
                {
                    last_deployment_update_modified = _last_deployment_update_modified;

                    setTableContent(content,"deploymentUpdateDetails","deploymentUpdateHeader")
                    setLastCheckedContent(content,"deploymentUpdateDateFormatted");
             
                    var deploymentUpdateStateElement = mx.$("#deploymentUpdateState");
                    var deploymentUpdateStateMessage = getContentValue(content,"deploymentUpdateState");
                    deploymentUpdateStateElement.style.display = deploymentUpdateStateMessage ? "" : "None";;
                    deploymentUpdateStateElement.innerHTML = deploymentUpdateStateMessage;
                }
                
                
                window.clearTimeout(workflowTimer);
                var updateWorkflowElement = mx.$("#updateWorkflow");
                var updateWorkflowContent = getContentValue(content,"updateWorkflow");
                updateWorkflowElement.innerHTML = updateWorkflowContent;
                updateWorkflowElement.style.display = updateWorkflowContent ? "" : "None";
                
                var updateWorkflowFallbackContent = getContentValue(content,"updateWorkflowFallback");
                if( updateWorkflowFallbackContent )
                {
                    workflowTimer = window.setTimeout(function()
                    {
                        updateWorkflowElement.innerHTML = updateWorkflowFallbackContent;
                        updateWorkflowElement.style.display = "";
                    },getContentValue(content,"updateWorkflowTimeout") * 1000);
                }
            }          
        }
        
        function loadData(new_data, callback)
        {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", mx.Host.getBase() + 'index_update.php');
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                  var content = document.createElement("div");
                  content.innerHTML = this.response;
                  
                  processData(new_data,content);
                  
                  callback();
                }
                else
                {
                    mx.Timer.register(function(){loadData(new_data,callback);}, 15000);
                }
            };
            xhr.send(JSON.stringify(new_data));
        }
        
        function handleDaemonState(state)
        {
            window.clearTimeout(refreshDaemonStateTimer);

            new_data = [];
            if( last_data_modified == null )
            {
                last_data_modified = state["last_data_modified"];
            }
            else
            {
                for( file in state["last_data_modified"])
                {
                    if( state["last_data_modified"][file] <= last_data_modified[file] )
                    {
                        continue;
                    }
                    last_data_modified[file] = state["last_data_modified"][file];
                    new_data.push(file);
                }
            }
            
            var daemonNeedsRestart = state["update_server_needs_restart"];
            var needsRestartElement = mx.$("#serverNeedsRestart");
            needsRestartElement.style.display = daemonNeedsRestart ? "flex" : "";
            
            job_is_running = state["job_is_running"];
            job_running_type = state["job_running_type"];
            job_cmd_name = state["job_cmd_name"];
            job_started = state["job_started"];
            
            last_job_status = state["last_job_status"];
            last_job_cmd_name = state["last_job_cmd_name"];
            last_job_duration = state["last_job_duration"];
                       
            var msg = "";
            var currentRunningStateElement = mx.$("#currentRunningState");
            var currentRunningActionsElement = mx.$("#currentRunningActions");
            if( job_is_running )
            {
                var logfile = state["job_logfile"];
                if( logfile )
                {
                    var logfile_name = logfile.substring(0,logfile.length - 4);
                    var data = logfile_name.split("-");

                    msg = "Currently a '<div class=\"detailView\" onClick=\"";
                    msg += "mx.UNCore.openDetails(this,'" + data[0] + "','" + data[3] + "','" + data[4] + "')";
                    msg += "\">" + job_cmd_name + "</div>' is running";
                    if( job_started ) 
                    {
                        var runtime = ( (new Date()).getTime() - Date.parse(job_started) ) / 1000;
                        runtime = Math.round(runtime * 10) / 10;
                        if( runtime > 0 ) msg += " since " + runtime + " seconds";
                    }
                    
                    currentRunningActionsElement.style.display= state["job_killable"] ? "block" : "";
                }
                else
                {
                    msg = "Currently a local started \"" + job_cmd_name + "\" is running";
                    currentRunningActionsElement.style.display= ""
                }
                
                currentRunningStateElement.innerHTML = msg;
                setExclusiveButtonsState(false);
                
                refreshDaemonStateTimer = window.setTimeout(refreshDaemonState, 1000);
            }
            else
            {
                currentRunningActionsElement.style.display="";
                currentRunningStateElement.innerHTML = "No update process is running";
                
                if( daemonNeedsRestart )
                {
                    setExclusiveButtonsState(false);
                    needsRestartElement.querySelector(".button").classList.remove("disabled");
                }
                else
                {
                    setExclusiveButtonsState(true);
                }

                refreshDaemonStateTimer = window.setTimeout(refreshDaemonState, 5000);
            }
           
            if( new_data.length > 0 ) loadData(new_data, function(){});
        }
        
        function handleDaemonError(msg, title)
        {
            var currentRunningStateElement = mx.$("#currentRunningState");
            var currentRunningActionsElement = mx.$("#currentRunningActions");
            currentRunningActionsElement.style.display="";
            currentRunningStateElement.innerHTML = "<div class=\"red\"><b>" + ( title ? title : "Daemon Error" ) + "</b><br>" + msg + "</div>";
            setExclusiveButtonsState(false)
        }
                                      
        function refreshDaemonState()
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
                        handleDaemonState(response);
                    }
                    else
                    {
                        handleDaemonError(response["message"])
                    }
                }
                else
                {
                    handleDaemonError(this.response, "Code: " + this.status + ", Message: '" + this.statusText + "'")
                    refreshDaemonStateTimer = window.setTimeout(refreshDaemonState, 15000);
                }
            };
            xhr.send(JSON.stringify({"action": "state"}));
        }
        
        function runAction(btn, action, parameter, response_callback)
        {
            btn.classList.add("disabled");
            
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
                            handleDaemonState(response);
                        }
                        else
                        {
                            handleServerError(response);
                        }
                    }
                    else
                    {
                        handleRequestError(this.status, this.statusText);
                    }
                }
            };
            xhr.send(JSON.stringify({"action": action, "parameter": parameter }));
        }
        
        function confirmAction(btn, action, parameter, confirm, button_color, response_callback )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            if( confirm )
            {
                var dialog = mx.Dialog.init({
                    title: "Are you sure?",
                    body: confirm,
                    buttons: [
                        { "text": "Continue", "class": button_color, "callback": function(){ dialog.close(); runAction(btn, action, parameter, response_callback); } },
                        { "text": "Cancel" },
                    ],
                    class: "confirmDialog",
                    destroy: true
                });
                dialog.open();
            }
            else
            {
                runAction(btn, action, parameter);
            }
        }

        ret.openDetails = function(event,datetime,cmd,username)
        {
            document.location = 'details.php?datetime=' + datetime + '&cmd=' + cmd + '&username=' + username;
        }

        function updateDialog(type, btn, callback )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            var passwordField = null;
            var passwordRemember = null;
            var passwordHint = null;
            var tagField = null;
            var confirmField = null;

            var body = "";
            if( type == "deployment" )
            {
                body += "You want to <b>install smartserver updates</b>?";            
            }
            else
            {
                body += "You want to update <b>everything</b>?";            
            }
            body += "<br><br><div class=\"form table\">";
            if( hasEncryptedVault )
            {
                var lastDeploymentPassword = sessionStorage.getItem("lastDeploymentPassword");
                
                body += "<div class=\"row\"><div>Password:</div><div>";
                body += "<input name=\"password\" type=\"password\" autocomplete=\"off\"";
                if( lastDeploymentPassword ) body += " value=\"" + lastDeploymentPassword + "\"";
                body += ">";
                body += "<br><input type=\"checkbox\" name=\"remember\"";
                if( lastDeploymentPassword ) body += " checked";
                body += "> Remember";
                body += "<div class=\"hint red\">Please enter a password</div>";
                body += "</div></div>";
            }
            
            if( type == "deployment" )
            {
                body += "<div class=\"row\"><div>Tags:</div><div><div class=\"autoCompletionSelection\"></div><input name=\"tag\"></div></div><div class=\"row\"><div>&nbsp;</div><div>&nbsp;</div></div></div><div class=\"deployConfirmation\"><input type=\"checkbox\" name=\"confirm\" checked> Mark all changes as deployed</div>";
            }
            
            var autocomplete = null;
            var dialog = mx.Dialog.init({
                title: "Are you sure?",
                body: body,
                buttons: [
                    { "text": "Continue", "class": "green", "callback": function(){ 
                        if( hasEncryptedVault && !passwordField.value )
                        {
                            passwordHint.style.maxHeight = passwordHint.scrollHeight + 'px';
                        }
                        else
                        {
                            parameter = {};
                            if( hasEncryptedVault )
                            {
                                passwordHint.style.maxHeight = 0;
                                parameter["password"] = passwordField.value;
                                if( passwordRemember.checked ) sessionStorage.setItem("lastDeploymentPassword", passwordField.value);
                                else sessionStorage.removeItem("lastDeploymentPassword");
                            }
                            
                            if( type == "deployment" )
                            {
                                var selectedTags = autocomplete.getSelectedValue();
                                autocomplete.setTopValues(selectedTags);
                                var selectedTagsAsString = selectedTags.join(",");
                                localStorage.setItem("lastSelectedDeploymentTags", selectedTagsAsString);
                                parameter["tags"] = selectedTagsAsString;
                                
                                parameter["confirm"] = confirmField.checked;
                            }

                            dialog.close(); 
                            
                            callback(parameter);
                        }
                    } },
                    { "text": "Cancel" },
                ],
                class: "confirmDialog",
                destroy: true
            });
            dialog.open();
            
            passwordField = dialog.getBody().querySelector("input[name=\"password\"]");
            passwordRemember = dialog.getBody().querySelector("input[name=\"remember\"]");
            passwordHint = dialog.getBody().querySelector(".hint");
            
            if( type == "deployment" )
            {
                tagField = dialog.getBody().querySelector("input[name=\"tag\"]");
                confirmField = dialog.getBody().querySelector("input[name=\"confirm\"]");    
                
                var lastSelectedTags = localStorage.getItem("lastSelectedDeploymentTags");
                
                autocomplete = mx.Autocomplete.init({
                    input: tagField,
                    values: deploymentTags,
                    top_values: lastSelectedTags ? lastSelectedTags.split(",") : [],
                    selectors: {
                        selectionLayer: ".autoCompletionSelection"
                    }
                });
                dialog.getRootLayer().addEventListener("destroy",autocomplete.destroy);
                
                function selectionHandler()
                {
                    if( autocomplete.getSelectedValue().length>0 ) confirmField.checked = false;
                    else confirmField.checked = true;
                }
                autocomplete.getRootLayer().addEventListener("selectionChanged",selectionHandler);
            }
        }
        
        ret.actionDeployUpdates = function(btn)
        {
            updateDialog("deployment",btn,function(parameter){
                runAction(btn, 'deploySmartserverUpdates', parameter); 
            });
        }
        
        ret.actionUpdateWorkflow = function(btn)
        {
            updateDialog("all",btn,function(parameter){
                runAction(btn, 'updateWorkflow', parameter); 
            });
        }
        
        ret.actionRebootSystem = function(btn)
        {
            confirmAction(btn,'systemReboot',null,'You want to <b>reboot your system</b>?',"red");          
        }
        
        ret.actionRestartServices = function(btn)
        {
            var service = btn.dataset.service;
            var msg = service.indexOf(',') != -1 ? 'all outdated services' : service;
            confirmAction(btn,'restartService',{'service': service},'You want to <b>restart ' + msg + '</b>?',"yellow");
        }
        
        ret.actionInstallUpdates = function(btn)
        { 
            confirmAction(btn,'installSystemUpdates',null,'You want to <b>install system updates<b>?',"green");          
        }
        
        ret.actionRefreshState = function(btn)
        {
            confirmAction(btn,'refreshSystemUpdateCheck');
        }
        
        ret.actionKillProcess = function(btn)
        {
            confirmAction(btn,'killProcess',null,'You want to kill current running job?',"red");
        }

        ret.actionRestartDaemon = function(btn)
        {
            window.clearTimeout(refreshDaemonStateTimer);
            confirmAction(btn,'restartDaemon',null,'You want to <b>restart update_daemon</b>?',"red", function(response){
                setExclusiveButtonsState(false)
                window.setTimeout(function(){ refreshDaemonState(); },2000);
            });
        }
        
        ret.toggle = function(btn,id)
        {
            var element = mx.$("#"+id);
            if( element.style.maxHeight )
            {
                element.style.maxHeight = "";
                window.setTimeout(function(){ element.style.display=""; setToogle(btn,element); },300);
            }
            else
            {
                element.style.display = "block";
                window.setTimeout(function(){ 
                    setScrollHeight(element);
                    setToogle(btn,element); 
                },0);
            }
        }

        ret.init = function()
        {
            processData(null,mx.$("#data"));
            
            var element = mx.$("#systemProcesses");
            if( element )
            {
                window.setTimeout(function(){ mx.$("#systemProcesses").click(); }, 100 );
            }
            refreshDaemonState();            
        }
        return ret;
    })( mx.UNCore || {} );
    
    mx.OnDocReady.push( mx.UNCore.init );
</script>
<div class="widget">
    <div class="header"><div>Daemon status</div><div></div></div>
    <div class="action" id="serverNeedsRestart"><div class="info red">Daemon was updated and needs to restart</div><div class="buttons"><div class="form button red exclusive" onclick="mx.UNCore.actionRestartDaemon(this)">Restart daemon</div></div></div>
    <div class="action" id="updateWorkflow"></div>
    <div class="action"><div class="info" id="currentRunningState"></div><div class="buttons" id="currentRunningActions"><div class="form button red" onclick="mx.UNCore.actionKillProcess(this)">Stop</div></div></div>
    <div class="action" id="lastRunningJobsHeader"></div>
    <div class="list form table logfileBox" id="lastRunningJobsDetails"></div>
</div>
<div class="widget">
    <div class="header"><div>System status</div><div id="systemStateDateFormatted"></div></div>
    <div class="action"><div class="info" id="lastUpdateDateFormatted"></div><div class="buttons"><div class="form button exclusive" onclick="mx.UNCore.actionRefreshState(this)">Refresh</div></div></div>
    <div class="action" id="systemRebootState"></div>
    <div class="action" id="systemStateHeader"></div>
    <div class="list form table" id="systemStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><div>System updates</div><div id="systemUpdateDateFormatted"></div></div>
    <div class="action" id="systemUpdateHeader"></div>
    <div class="list form table" id="systemUpdateDetails"></div>
</div>
<div class="widget">
    <div class="header"><div>Smartserver updates</div><div id="deploymentUpdateDateFormatted"></div></div>
    <div class="action" id="deploymentUpdateState"></div>
    <div class="action" id="deploymentUpdateHeader"></div>
    <div class="list form table" id="deploymentUpdateDetails"></div>
</div>
<?php 
  echo IndexTemplate::dump($system_state_file,$deployment_state_file,$deployment_tags_file,$deployment_logs_folder,NULL);
?>
</body>
</html>
