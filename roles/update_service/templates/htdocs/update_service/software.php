<?php
require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

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
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/update_service/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/update_service/'); ?>"></script>
</head>
<body class="inline software spacer-800">
<script>
var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
if( theme ) document.body.classList.add(theme);

mx.SNCore = (function( ret ) {
  
    var daemonApiUrl = mx.Host.getBase() + '../api.php'; 
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
                    mx.UpdateServiceHelper.handleServerError(response["message"]);
                }
            }
            else if( this.status == 503 ) 
            {
                mx.UpdateServiceHelper.handleServerNotAvailable();
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(last_data_modified, callback) }, 15000);
            }
            else
            {
                if( this.status != 0 && this.status != 401 ) mx.UpdateServiceHelper.handleRequestError(this.status, this.statusText, this.response);
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(last_data_modified, callback) }, 15000);
            }
        };
        
        xhr.send(JSON.stringify({"action": "state", "parameter": { "type": "software", "last_data_modified": last_data_modified }}));
    }
    
    ret.startSoftwareCheck = function()
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
        };
        
        xhr.send(JSON.stringify({"action": "refreshSoftwareVersionCheck"}));
    }
        
    ret.init = function()
    { 
        refreshDaemonState(null, function(){}); 
        
        mx.Page.init();
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
<div class="list"></div>
<div class="error"></div>
</body>
</html>
