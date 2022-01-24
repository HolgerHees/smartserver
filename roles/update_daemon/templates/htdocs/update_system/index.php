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
        
        var daemonApiUrl = mx.Host.getBase() + 'api.php';
    
        function handleServerError( response )
        {
            alert(response["message"]);
        }
        
        function handleRequestError( code, text )
        {
            alert("error '" + code + " " + text + "'");
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
                  
                  hasEncryptedVault = content.querySelector("#hasEncryptedVault").innerHTML == '1' ? true : false;
                  
                  mx.$("#lastUpdate").innerHTML = "Last full refresh " + content.querySelector("#lastUpdates").innerHTML;
                  
                  
                  _last_system_state_modified = content.querySelector("#systemStateTimestamp").innerHTML;
                  if( last_system_state_modified == null || last_system_state_modified != _last_system_state_modified )
                  {
                      var rebootNeededElement = mx.$("#rebootNeeded");
                      var rebootNeededContent = content.querySelector("#rebootNeeded").innerHTML;
                      rebootNeededElement.innerHTML = rebootNeededContent;
                      rebootNeededElement.style.display = rebootNeededContent ? "" : "None";
                      
                      mx.$("#systemState").innerHTML = content.querySelector("#systemState").innerHTML;
                      var systemStateDetailsElement = mx.$("#systemStateDetails");
                      systemStateDetailsElement.innerHTML = content.querySelector("#systemStateDetails").innerHTML;
                      last_system_state_modified = _last_system_state_modified;
                      setToogle(mx.$("#systemState .form.button.toggle"),systemStateDetailsElement);
                      fixScrollHeight(systemStateDetailsElement);
                      
                      mx.$("#lastSystemStateCheck").innerHTML = "(Last checked " + content.querySelector("#systemStateFmt").innerHTML + ")";
                      
                  }
                  
                  _last_system_update_modified = content.querySelector("#systemUpdateTimestamp").innerHTML;
                  if( last_system_update_modified == null || last_system_update_modified != _last_system_update_modified )
                  {
                      mx.$("#systemUpdate").innerHTML = content.querySelector("#systemUpdate").innerHTML;
                      var systemUpdateDetailsElement = mx.$("#systemUpdateDetails");
                      systemUpdateDetailsElement.innerHTML = content.querySelector("#systemUpdateDetails").innerHTML;
                      last_system_update_modified = _last_system_update_modified;
                      setToogle(mx.$("#systemUpdate .form.button.toggle"),systemUpdateDetailsElement);
                      fixScrollHeight(systemUpdateDetailsElement);

                      mx.$("#lastSystemUpdateCheck").innerHTML = "(Last checked " + content.querySelector("#systemUpdateFmt").innerHTML + ")";
                  }

                  _last_deployment_update_modified = content.querySelector("#deploymentUpdateTimestamp").innerHTML;
                  if( last_deployment_update_modified == null || last_deployment_update_modified != _last_deployment_update_modified )
                  {
                      deploymentUpdateInfoCodes = {
                          "failed": ["red","Skipped git pull (broken remote ci tests)"],
                          "pending": ["yellow","Skipped git pull (some remote ci pending)"],
                          "pulled": ["green", "Git pulled (all remote ci succeeded)"],
                          "uncommitted": ["red","Skipped git pull (has uncommitted changes)"]
                      };
                      
                      var deploymentUpdateInfoCode = content.querySelector("#deploymentUpdateInfo").innerHTML;
                      var deploymentUpdateData = deploymentUpdateInfoCodes[deploymentUpdateInfoCode];
                      var deploymentUpdateElement = mx.$("#deploymentUpdateInfo");
                      deploymentUpdateElement.innerHTML = deploymentUpdateData[1] + ". Last git pull was on " + content.querySelector("#deploymentUpdatePullDate").innerHTML + ".";
                      deploymentUpdateElement.classList.remove("green");
                      deploymentUpdateElement.classList.remove("yellow");
                      deploymentUpdateElement.classList.remove("red");
                      deploymentUpdateElement.classList.add(deploymentUpdateData[0]);
                    
                      mx.$("#deploymentUpdate").innerHTML = content.querySelector("#deploymentUpdate").innerHTML;
                      var deploymentUpdateDetailsElement = mx.$("#deploymentUpdateDetails");
                      deploymentUpdateDetailsElement.innerHTML = content.querySelector("#deploymentUpdateDetails").innerHTML;
                      last_deployment_update_modified = _last_deployment_update_modified;
                      setToogle(mx.$("#deploymentUpdate .form.button.toggle"),deploymentUpdateDetailsElement);
                      fixScrollHeight(deploymentUpdateDetailsElement);

                      mx.$("#lastDeploymentUpdateCheck").innerHTML = "(Last checked " + content.querySelector("#deploymentUpdateFmt").innerHTML + ")";
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
            
            var lastRunningElement = mx.$("#lastRunningState");
            if( last_job_cmd_name )
            {
                var msg = "Last '" + last_job_cmd_name + "' " + ( last_job_status == "0" ? "was successful" : "failed" );
                msg += " after " + Math.round(last_job_duration * 10) / 10 + " seconds";
                lastRunningElement.innerHTML = msg;
                if( last_job_status == 0 ) lastRunningElement.classList.remove("red");
                else lastRunningElement.classList.add("red");
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
                detailElement.style.maxHeight = ( detailElement.scrollHeight + 20 ) + "px";
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
        
        function runAction(btn, action, parameter)
        {
            btn.classList.add("disabled");
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", daemonApiUrl );
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
                    handleRequestError(this.status, this.statusText);
                }
            };
            xhr.send(JSON.stringify({"action": action, "parameter": parameter }));
        }
        
        function confirmAction(btn, action, parameter, confirm, button_color )
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
                        { "text": "Continue", "class": button_color, "callback": function(){ dialog.close(); runAction(btn, action, parameter); } },
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
            var passwordHint = null;
            var tagField = null;
            var confirmField = null;

            var body = "You want to <b>deploy smartserver changes</b>?<br><br><div class=\"form table\">";            
            if( hasEncryptedVault )
            {
                body += "<div class=\"row\"><div>Password:</div><div><input name=\"password\" type=\"password\" autocomplete=\"off\"><div class=\"hint red\">Please enter a password</div></div></div>";
            }
            body += "<div class=\"row\"><div>Tags:</div><div><input name=\"tag\"></div></div><div class=\"row\"><div>&nbsp;</div><div>&nbsp;</div></div></div><div class=\"deployConfirmation\"><input type=\"checkbox\" name=\"confirm\" checked> Mark all changes as deployed</div>";
            
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
                            }
                            parameter["tags"] = tagField.value;
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
            passwordHint = dialog.getBody().querySelector(".hint");
            tagField = dialog.getBody().querySelector("input[name=\"tag\"]");
            confirmField = dialog.getBody().querySelector("input[name=\"confirm\"]");    
            
            function tagInputHandler()
            {
                if( tagField.value ) confirmField.checked = false;
                else confirmField.checked = true;
            }
            tagField.addEventListener("keyup",tagInputHandler);
            tagField.addEventListener("change",tagInputHandler);
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
    <div class="action"><div class="info" id="currentRunningState"></div></div>
    <div class="action"><div class="info" id="lastRunningState"></div></div>
</div>
<div class="widget">
    <div class="header"><span>System status</span><span id="lastSystemStateCheck"></span></div>
    <div class="action"><div class="info" id="lastUpdate"></div><div class="buttons"><div class="form button" onclick="mx.UNCore.actionRefreshState(this)">Refresh</div></div></div>
    <div class="action" id="rebootNeeded"></div>
    <div class="action" id="systemState"></div>
    <div class="list form table" id="systemStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><span>System updates</span><span id="lastSystemUpdateCheck"></span></div>
    <div class="action" id="systemUpdate"></div>
    <div class="list form table" id="systemUpdateDetails"></div>
</div>
<div class="widget">
    <div class="header"><span>Deployment updates</span><span id="lastDeploymentUpdateCheck"></span></div>
    <div class="action" id="deploymentUpdateInfo"></div>
    <div class="action" id="deploymentUpdate"></div>
    <div class="list form table" id="deploymentUpdateDetails"></div>
</div>
</body>
</html>
