<?php
require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
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
        
        var daemonApiUrl = mx.Host.getBase() + 'api.php';
    
        function handleServerError( response )
        {
            alert(response["message"]);
        }
        
        function handleRequestError( code, text )
        {
            alert("error '" + code + " " + text + "'");
        }
        
        function getContentValue(content,id)
        {
            return content.querySelector(id).innerHTML;
        }
        
        function setTableContent(content,tableId,headerId)
        {
            mx.$(headerId).innerHTML = content.querySelector(headerId).innerHTML;
                      
            var systemStateDetailsElement = mx.$(tableId);
            systemStateDetailsElement.innerHTML = content.querySelector(tableId).innerHTML;
            setToogle(mx.$(headerId + " .form.button.toggle"),systemStateDetailsElement);
            fixScrollHeight(systemStateDetailsElement);
        }

        function setLastCheckedContent(content,id)
        {
            var element = mx.$(id)
            var last = content.querySelector(id).innerHTML;
            if( last ) element.innerHTML = "(Last checked " + last + ")";
            else element.innerHTML = "(Was never checked)";
        }
        
        function loadData(callback)
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
                  
                  hasEncryptedVault = getContentValue(content,"#hasEncryptedVault") == '1' ? true : false;
                  
                  mx.$("#lastUpdateDateFormatted").innerHTML = "Last full refresh " + getContentValue(content,"#lastUpdateDateFormatted");
                  
                  _last_system_state_modified = getContentValue(content,"#systemStateDateAsTimestamp");
                  if( last_system_state_modified == null || last_system_state_modified != _last_system_state_modified )
                  {
                      var rebootNeededElement = mx.$("#systemRebootNeeded");
                      var rebootNeededContent = getContentValue(content,"#systemRebootNeeded");
                      rebootNeededElement.innerHTML = rebootNeededContent;
                      rebootNeededElement.style.display = rebootNeededContent ? "" : "None";
                      
                      last_system_state_modified = _last_system_state_modified;
                     
                      setTableContent(content,"#systemStateDetails","#systemStateHeader")
                      setLastCheckedContent(content,"#systemStateDateFormatted");
                  }
                  
                  _last_system_update_modified = getContentValue(content,"#systemUpdateDateAsTimestamp");
                  if( last_system_update_modified == null || last_system_update_modified != _last_system_update_modified )
                  {
                      last_system_update_modified = _last_system_update_modified;
                      
                      setTableContent(content,"#systemUpdateDetails","#systemUpdateHeader")
                      setLastCheckedContent(content,"#systemUpdateDateFormatted");
                  }

                  _last_deployment_update_modified = getContentValue(content,"#deploymentUpdateDateAsTimestamp");
                  if( last_deployment_update_modified == null || last_deployment_update_modified != _last_deployment_update_modified )
                  {
                      deploymentUpdateInfoCodes = {
                          "failed": ["red","Skipped git pull (broken remote ci tests)"],
                          "pending": ["yellow","Skipped git pull (some remote ci pending)"],
                          "pulled": ["green", "Git pulled (all remote ci succeeded)"],
                          "uncommitted": ["red","Skipped git pull (has uncommitted changes)"]
                      };
                      
                      var deploymentUpdateElement = mx.$("#deploymentUpdateStatusInfo");
                      var deploymentUpdateStatusCode = getContentValue(content,"#deploymentUpdateStatusCode");
                      var deploymentUpdateData = deploymentUpdateInfoCodes[deploymentUpdateStatusCode];
                      if( deploymentUpdateData )
                      {
                          deploymentUpdateElement.style.display = "";
                          deploymentUpdateElement.innerHTML = deploymentUpdateData[1] + ". Last git pull was on " + getContentValue(content,"#deploymentUpdateLastPullDate") + ".";
                          ["green","yellow","red"].forEach(function(color){ deploymentUpdateElement.classList.remove(color); });
                          deploymentUpdateElement.classList.add(deploymentUpdateData[0]);
                      }
                      else
                      {
                          deploymentUpdateElement.style.display = "none";
                      }
                      last_deployment_update_modified = _last_deployment_update_modified;

                      setTableContent(content,"#deploymentUpdateDetails","#deploymentUpdateHeader")
                      setLastCheckedContent(content,"#deploymentUpdateDateFormatted");
                 
                      deploymentTags = getContentValue(content,"#deploymentTags").split(",");
                  }
                  
                  callback();
                }
                else
                {
                    mx.Timer.register(function(){loadData();}, 15000);
                }
            };
            xhr.send();
        }
        
        function handleDaemonState(state)
        {
            window.clearTimeout(refreshDaemonStateTimer);

            has_new_data = last_data_modified != null && last_data_modified != state["last_data_modified"];
          
            mx.$("#serverNeedsRestart").style.display = state["update_server_needs_restart"] ? "flex" : "";
            
            job_is_running = state["job_is_running"];
            job_running_type = state["job_running_type"];
            job_cmd_name = state["job_cmd_name"];
            job_started = state["job_started"]

            last_data_modified = state["last_data_modified"];
             
            last_job_status = state["last_job_status"];
            last_job_cmd_name = state["last_job_cmd_name"];
            last_job_duration = state["last_job_duration"];
            
            var currentRunningElement = mx.$("#currentRunningState");
            if( job_is_running )
            {
                msg = "Currently a '" + job_cmd_name + "' is running";
                if( job_started ) 
                {
                    var runtime = ( (new Date()).getTime() - Date.parse(job_started) ) / 1000;
                    runtime = Math.round(runtime * 10) / 10;
                    if( runtime > 0 ) msg += " since " + runtime + " seconds";
                }
              
                currentRunningElement.classList.add("green");
                currentRunningElement.innerHTML = msg;
                mx.$$("div.form.button").forEach(function(element){ element.classList.add("disabled"); });

                refreshDaemonStateTimer = window.setTimeout(refreshDaemonState, 1000);
            }
            else
            {
                currentRunningElement.classList.remove("green");
                currentRunningElement.innerHTML = "No update or deployment process is running";
                mx.$$("div.form.button").forEach(function(element){ element.classList.remove("disabled"); });

                refreshDaemonStateTimer = window.setTimeout(refreshDaemonState, 5000);
            }
            
            var lastRunningBlock = mx.$("#lastRunningStateBlock");
            if( last_job_cmd_name )
            {
                lastRunningBlock.style.display = "";
                var lastRunningElement = mx.$("#lastRunningState");
                var msg = "Last '" + last_job_cmd_name + "' " + ( last_job_status == "0" ? "was successful" : "failed" );
                msg += " after " + Math.round(last_job_duration * 10) / 10 + " seconds";
                lastRunningElement.innerHTML = msg;
                if( last_job_status == 0 ) lastRunningElement.classList.remove("red");
                else lastRunningElement.classList.add("red");
            }
            else
            {
                lastRunningBlock.style.display = "None";
            }
            
            if( has_new_data )
            {
                loadData(function(){
                  
                });
            }
        }
    
        function fixScrollHeight(detailElement)
        {
            if( detailElement.style.maxHeight )
            {
                if( detailElement.innerHTML )
                {
                    detailElement.style.maxHeight = ( detailElement.scrollHeight + 20 ) + "px";
                }
                else
                {
                    detailElement.style.maxHeight = "";
                    detailElement.style.display = "";
                }
            }
        }
        
        function setToogle(btnElement,detailElement)
        {
            if( btnElement != null )
            {
                btnElement.innerText = detailElement.style.maxHeight ? "Hide" : "Show";
            }
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
                        handleServerError(response);
                    }
                }
                else
                {
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

        ret.actionDeployUpdates = function(btn)
        {
            var passwordField = null;
            var passwordRemember = null;
            var passwordHint = null;
            var tagField = null;
            var confirmField = null;

            var body = "You want to <b>deploy smartserver changes</b>?<br><br><div class=\"form table\">";            
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
            body += "<div class=\"row\"><div>Tags:</div><div><div class=\"autoCompletionSelection\"></div><input name=\"tag\"></div></div><div class=\"row\"><div>&nbsp;</div><div>&nbsp;</div></div></div><div class=\"deployConfirmation\"><input type=\"checkbox\" name=\"confirm\" checked> Mark all changes as deployed</div>";
            
            var autocomplete = null;
            var dialog = mx.Dialog.init({
                title: "Are you sure?",
                body: body,
                buttons: [
                    { "text": "Continue", "class": "red", "callback": function(){ 
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
                                                       
                            var selectedTags = autocomplete.getSelectedValue();
                            autocomplete.setTopValues(selectedTags);
                            var selectedTagsAsString = selectedTags.join(",");
                            localStorage.setItem("lastSelectedDeploymentTags", selectedTagsAsString);
                            parameter["tags"] = selectedTagsAsString;
                            
                            parameter["confirm"] = confirmField.checked;

                            dialog.close(); 
                            runAction(btn, 'deploySmartserverUpdates', parameter); 
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
        
        ret.actionRebootSystem = function(btn)
        {
            confirmAction(btn,'systemReboot',null,'You want to <b>reboot your system</b>?',"red");          
        }
        
        ret.actionRestartServices = function(btn)
        {
            var service = btn.dataset.service;
            var msg = service.indexOf(',') != -1 ? 'all outdated services' : service;
            confirmAction(btn,'restartService',{'service': service},'You want to <b>restart ' + msg + '</b>?',"yellow")
        }
        
        ret.actionInstallUpdates = function(btn)
        { 
            confirmAction(btn,'installSystemUpdates',null,'You want to <b>install system updates<b>?',"red");          
        }
        
        ret.actionRefreshState = function(btn)
        {
            confirmAction(btn,'refreshSystemUpdateCheck')
        }
        
        ret.actionRestartDaemon = function(btn)
        {
            window.clearTimeout(refreshDaemonStateTimer);
            confirmAction(btn,'restartService',{'service': 'update_daemon'},'You want to <b>restart update_daemon</b>?',"red", function(response){
                mx.$$("div.form.button").forEach(function(element){ element.classList.add("disabled"); });
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
                window.setTimeout(function(){ element.style.maxHeight = ( element.scrollHeight + 20 ) + "px"; setToogle(btn,element); },0);
            }
        }

        ret.init = function()
        {
            loadData(function()
            {
                var element = mx.$("#systemProcesses");
                if( element )
                {
                    window.setTimeout(function(){ mx.$("#systemProcesses").click(); }, 100 );
                }
            });
            refreshDaemonState();            
        }
        return ret;
    })( mx.UNCore || {} );
    
    mx.OnDocReady.push( mx.UNCore.init );
</script>
<div class="widget">
    <div class="header"><span>Daemon status</span><span></span></div>
    <div class="action" id="serverNeedsRestart"><div class="info red">Daemon was updated and needs to restart</div><div class="buttons"><div class="form button red" onclick="mx.UNCore.actionRestartDaemon(this)">Restart daemon</div></div></div>
    <div class="action"><div class="info" id="currentRunningState"></div></div>
    <div class="action" id="lastRunningStateBlock"><div class="info" id="lastRunningState"></div></div>
</div>
<div class="widget">
    <div class="header"><span>System status</span><span id="systemStateDateFormatted"></span></div>
    <div class="action"><div class="info" id="lastUpdateDateFormatted"></div><div class="buttons"><div class="form button" onclick="mx.UNCore.actionRefreshState(this)">Refresh</div></div></div>
    <div class="action" id="systemRebootNeeded"></div>
    <div class="action" id="systemStateHeader"></div>
    <div class="list form table" id="systemStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><span>System updates</span><span id="systemUpdateDateFormatted"></span></div>
    <div class="action" id="systemUpdateHeader"></div>
    <div class="list form table" id="systemUpdateDetails"></div>
</div>
<div class="widget">
    <div class="header"><span>Deployment updates</span><span id="deploymentUpdateDateFormatted"></span></div>
    <div class="action" id="deploymentUpdateStatusInfo"></div>
    <div class="action" id="deploymentUpdateHeader"></div>
    <div class="list form table" id="deploymentUpdateDetails"></div>
</div>
</body>
</html>
