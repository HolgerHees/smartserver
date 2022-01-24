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
        var is_running = null;
        var running_type = null;
        var cmd_name = null;
        var last_modifiled = null;
        var last_system_state_modified = null;
        var last_system_update_modified = null;
        var last_deployment_update_modified = null;
        
        var daemonApiUrl = mx.Host.getBase() + 'api.php';
    
        handleError = function( code, text )
        {
            alert("error '" + code + " " + text + "'");
        }
        
        loadData = function(callback)
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
                  
                  mx.$("#lastUpdate").innerHTML = content.querySelector("#lastUpdates").innerHTML;
                  
                  
                  _last_system_state_modified = content.querySelector("#systemStateTimestamp").innerHTML;
                  if( last_system_state_modified == null || last_system_state_modified != _last_system_state_modified )
                  {
                      mx.$("#rebootNeeded").innerHTML = content.querySelector("#rebootNeeded").innerHTML;
                      mx.$("#systemState").innerHTML = content.querySelector("#systemState").innerHTML;
                      var systemStateDetailsElement = mx.$("#systemStateDetails");
                      systemStateDetailsElement.innerHTML = content.querySelector("#systemStateDetails").innerHTML;
                      last_system_state_modified = _last_system_state_modified;
                      setToogle(mx.$("#systemState .form.button.toggle"),systemStateDetailsElement);
                      fixScrollHeight(systemStateDetailsElement);
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
                  }

                  _last_deployment_update_modified = content.querySelector("#deploymentUpdateTimestamp").innerHTML;
                  if( last_deployment_update_modified == null || last_deployment_update_modified != _last_deployment_update_modified )
                  {
                      mx.$("#deploymentUpdate").innerHTML = content.querySelector("#deploymentUpdate").innerHTML;
                      var deploymentUpdateDetailsElement = mx.$("#deploymentUpdateDetails");
                      deploymentUpdateDetailsElement.innerHTML = content.querySelector("#deploymentUpdateDetails").innerHTML;
                      last_deployment_update_modified = _last_deployment_update_modified;
                      setToogle(mx.$("#deploymentUpdate .form.button.toggle"),deploymentUpdateDetailsElement);
                      fixScrollHeight(deploymentUpdateDetailsElement);
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
        
        handleDaemonState = function(state)
        {
            has_new_data = last_modifiled != null && last_modifiled != state["last_modified"];
          
            is_running = state["is_running"];
            running_type = state["running_type"];
            cmd_name = state["cmd_name"];
            last_modifiled = state["last_modified"];
             
            last_status = state["last_status"];
            last_cmd_name = state["last_cmd_name"];
            
            var element = mx.$("#runningState");
            if( is_running )
            {
                element.classList.add("red");
                element.innerHTML = "Currently a '" + cmd_name + ( running_type ? "' (" + running_type + ")" : "" ) + " is running";
                mx.$$("div.form.button").forEach(function(element){ element.classList.add("disabled"); });
            }
            else
            {
                element.classList.remove("red");
                var msg = "No update or deployment process is running";
                if( last_cmd_name ) msg += " (Last '" + last_cmd_name + "' " + ( last_status == "0" ? "was successful" : "failed" ) + ")";
                element.innerHTML = msg;
                mx.$$("div.form.button").forEach(function(element){ element.classList.remove("disabled"); });
            }
            
            if( has_new_data )
            {
                loadData(function(){
                  
                });
            }
        }
    
        refreshDaemonState = function()
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
                        mx.Timer.register(function(){refreshDaemonState();}, is_running ? 1000 : 5000);
                    }
                    else
                    {
                        mx.Timer.register(function(){refreshDaemonState();}, 15000);
                    }
                }
                else
                {
                    mx.Timer.register(function(){refreshDaemonState();}, 15000);
                }
            };
            xhr.send(JSON.stringify({"action": "state"}));
        }
        
        fixScrollHeight = function(detailElement)
        {
            if( detailElement.style.maxHeight )
            {
                detailElement.style.maxHeight = ( detailElement.scrollHeight + 20 ) + "px";
            }
        }
        
        setToogle = function(btnElement,detailElement)
        {
            if( btnElement != null )
            {
                btnElement.innerText = detailElement.style.maxHeight ? "Hide" : "Show";
            }
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
        
        runAction = function(btn, action, parameter)
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
                    handleDaemonState(response);
                }
                else
                {
                    handleError(this.status, this.statusText);
                }
            };
            xhr.send(JSON.stringify({"action": action, "parameter": parameter }));
        }
        
        ret.actionSmartserverUpdateDialog = function(btn, action)
        {
            var dialog = mx.Dialog.init({
                body: "Are you sure?<br>Password: <input name\"password\" type=\"password\" autocomplete=\"off\"><br>Tags: <input name\"tags\">",
                buttons: [
                    { "text": "Continue", "class": "red", "callback": function(){ 
                        //console.log(dialog.getBody().querySelector("").value())
                        runAction(btn, action, null); 
                    } },
                    { "text": "Cancel" },
                ],
                class: "confirmDialog",
                destroy: true
            });
            dialog.open();
        }
        ret.action = function(btn, action, parameter, confirm )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            if( confirm )
            {
                var dialog = mx.Dialog.init({
                    body: "Are you sure?",
                    buttons: [
                        { "text": "Continue", "class": "red", "callback": function(){ runAction(btn, action, parameter); } },
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
    <h1>System status</h1>
    <div class="action"><div class="info" id="runningState"></div></div>
    <div class="action"><div class="info" id="lastUpdate"></div><div class="buttons"><div class="form button" onclick="mx.UNCore.action(this,'refreshSystemUpdateCheck',false)">Refresh</div></div></div>
    <div class="action" id="rebootNeeded"></div>
    <div class="action" id="systemState"></div>
    <div class="form table" id="systemStateDetails"></div>
</div>
<div class="widget">
    <h1>Updates</h1>
    <div class="action" id="systemUpdate"></div>
    <div class="form table" id="systemUpdateDetails"></div>
    <div class="action" id="deploymentUpdate"></div>
    <div class="form table" id="deploymentUpdateDetails"></div>
</div>
</body>
</html>
