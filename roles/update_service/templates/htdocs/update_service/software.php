<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link href="<?php echo Ressources::getCSSPath('/update_service/'); ?>" rel="stylesheet">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/update_service/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/update_service/'); ?>"></script>
<script>
mx.SNCore = (function( ret ) {
  
    var daemonApiUrl = mx.Host.getBase() + '../api/'; 
    var refreshDaemonStateTimer = 0;
        
    function handleDaemonState(state)
    {
        window.clearTimeout(refreshDaemonStateTimer);
        
        //console.log(state);
        
        if( state["job_is_running"] )
        {
            refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 1000);
        }
        else
        {
            refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
        }

        if( state["job_is_running"] && state["job_cmd_type"] == "software_check" ) mx.SoftwareVersionsTemplates.setLoadingGear(state["job_started"]);
        else if( Object.keys(state["changed_data"]).length > 0 ) mx.SoftwareVersionsTemplates.processData(state["last_data_modified"], state["changed_data"] );
             
        mx.Page.refreshUI();
    }
    
    function refreshDaemonState(last_data_modified,callback)
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl + "state/" );
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    mx.Error.confirmSuccess();
                    
                    handleDaemonState(response);
                    
                    if( callback ) callback();
                }
                else
                {
                    mx.Error.handleServerError(response["message"]);
                }
            }
            else
            {
                let timeout = 15000;
                if( this.status == 0 || this.status == 503 ) 
                {
                    mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
                }
                else
                {
                    if( this.status != 401 ) mx.Error.handleRequestError(this.status, this.statusText, this.response);
                }
                
                refreshDaemonStateTimer = mx.Page.handleRequestError(this.status,daemonApiUrl,function(){ refreshDaemonState(last_data_modified, callback) }, timeout);
            }
        };
        
        xhr.send(mx.Core.encodeDict( { "type": "software", "last_data_modified": last_data_modified } ));
    }
    
    ret.startSoftwareCheck = function()
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl + "refreshSoftwareVersionCheck/" );
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    mx.Error.confirmSuccess();
                    
                    handleDaemonState(response);
                }
                else
                {
                    mx.Error.handleServerError(response["message"]);
                }
            }
            else
            {
                mx.Error.handleRequestError(this.status, this.statusText, this.response);
            }
        };
        
        xhr.send();
    }
        
    ret.init = function()
    { 
        refreshDaemonState(null, function(){}); 
        
        mx.Page.refreshUI();
    }
    
    ret.openUrl = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }
    
    return ret;
})( mx.SNCore || {} );
    
mx.OnDocReady.push( mx.SNCore.init );


</script>
</head>
<body class="software">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer-800", mx.I18N.get("Software")); } );</script>
<div class="list"></div>
<div class="contentLayer error"></div>
</body>
</html>
