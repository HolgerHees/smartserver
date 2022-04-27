mx.UpdateServiceActions = (function( ret ) { 
  
    var dialog = null;
    
    var daemonApiUrl = null; 
        
    function runAction(btn, action, parameter, response_callback)
    {
        if( !parameter ) parameter = {};
        parameter["last_data_modified"] = mx.UNCore.getLastDataModified();

        mx.UNCore.setUpdateJobStarted( parameter.hasOwnProperty("system_updates_hash") || parameter.hasOwnProperty("smartserver_changes_hash") );
        
        // needs to be asynchrone to allow ripple effect
        window.setTimeout(function() { btn.classList.add("disabled"); },0);
        
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl + action + "/" );
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        
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
                        mx.Error.confirmSuccess();

                        mx.UNCore.handleDaemonState(response);
                    }
                    else
                    {
                        mx.Error.handleServerError(response["message"]);
                    }
                }
                else if( this.status == 0 || this.status == 503 ) 
                {
                    mx.Error.handleError( mx.I18N.get( mx.UpdateServiceHelper.isRestarting() ? "Service is restarting" : "Service is currently not available")  );
                }
                else
                {
                    mx.Error.handleRequestError(this.status, this.statusText, this.response);
                }
            }
        };
        
        xhr.send(mx.Core.encodeDict(parameter));
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
            body += "<br>";
        }
        else
        {
            body += mx.I18N.get("You want to <span class='important'>update everything</span>? This includes the following steps:");     
            
            body += "<ul>";
            body += "<li>" + mx.I18N.get("Check for updates again") + "</li>";
            if( mx.UNCore.getSystemUpdatesCount() > 0 )
            {
                body += "<li>" + mx.I18N.get("Installation of system updates") + "</li>";
                body += "<li>" + mx.I18N.get("Reboot if necessary") + "</li>";
                body += "<li>" + mx.I18N.get("Restart services if necessary") + "</li>";
            }
            if( mx.UNCore.getSmartserverChangesCount() > 0 )
            {
                body += "<li>" + mx.I18N.get("Installation of smart server updates") + "</li>";
            }
            body += "</ul>";
        }
        
        //body += "<br>";
        
        let hasEncryptedVault = mx.UNCore.hasEncryptedVault();
        let deploymentTags = mx.UNCore.getDeploymentTags();
        let hasPasswordField = hasEncryptedVault;
        let hasTagField = type == "deployment" && !has_tags;
        
        if( hasPasswordField || hasTagField )
        {
            body += "<br><div class=\"form table\">";
            
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
                        
                        if( args )
                        {
                            if( args.hasOwnProperty("system_updates_hash") ) parameter["system_updates_hash"] = args["system_updates_hash"];
                            if( args.hasOwnProperty("smartserver_changes_hash") ) parameter["smartserver_changes_hash"] = args["smartserver_changes_hash"];
                        }
                        
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
                //console.log(event);
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
                                    //console.log(value);
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
                    if( !event["detail"]["added"] && event["detail"]["value"] == "all" )
                    {
                        confirmField.checked = false;
                    }
                    confirmField.disabled = false;
                }
                //if( autocomplete.getSelectedValues().length>0 ) confirmField.checked = false;
                //else confirmField.checked = true;
              
            }
            autocomplete.getRootLayer().addEventListener("selectionChanged",selectionHandler);
        }
    }     
        
    ret.actionUpdateWorkflow = function(btn)
    {
        updateDialog("all",btn,mx.UNCore.getUpdateHashes(),function(parameter){
            runAction(btn, 'updateWorkflow', parameter); 
        });
    }
    
    ret.actionInstallUpdates = function(btn)
    { 
        confirmAction(btn,'installSystemUpdates',mx.UNCore.getUpdateHashes(),mx.I18N.get("You want to <span class='important'>install system updates</span>?"),"green");          
    }
    
    ret.actionDeployUpdates = function(btn)
    {
        var tag = btn.dataset.tag;
        parameter = tag ? { "tags": tag } : null;
        updateDialog("deployment",btn,parameter,function(parameter){
            runAction(btn, 'deploySmartserverUpdates', parameter); 
        });
    }
    
    ret.actionRefreshUpdateState = function(btn,type)
    { 
        confirmAction(btn,'refreshSystemUpdateCheck', type ? { "type": type } : {} );
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
    
    ret.openDetails = function(event,datetime,cmd,username)
    {
        document.location = '../details/?datetime=' + datetime + '&cmd=' + cmd + '&username=' + username;
    }

    ret.openGitCommit = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }

    ret.getDialog = function()
    {
        return dialog;
    }
    
    ret.init = function( _daemonApiUrl )
    {
        daemonApiUrl = _daemonApiUrl;
    }

    return ret;
    
})( mx.UpdateServiceActions || {} ); 
