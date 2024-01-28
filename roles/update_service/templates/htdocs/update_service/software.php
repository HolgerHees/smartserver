<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/update_service/"]); ?>
<script>
mx.SNCore = (function( ret ) {
  
    var daemonApiUrl = mx.Host.getBase() + '../api/';
    var jobtimer = null;

    function setLoadingGear(data)
    {
        mx.SoftwareVersionsTemplates.setLoadingGear(data);
        jobtimer = window.setTimeout(function(){ setLoadingGear(data); }, 1000);
    }

    function jobStatus(data)
    {
        if( data["job"] != "software_check" ) return;

        if( data["state"] == "running" ) setLoadingGear(data["started"]);
    }

    function processData(data)
    {
        if( jobtimer ) window.clearTimeout(jobtimer);

        mx.SoftwareVersionsTemplates.processData(data)
        mx.Page.refreshUI();
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
                if( response["status"] == "0" ) mx.Error.confirmSuccess();
                else mx.Error.handleServerError(response["message"]);
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
        let socket = mx.ServiceSocket.init('update_service');
        socket.on("connect", (socket) => socket.emit('initSoftware'));
        socket.on("initSoftware", (data) => processData( data ) );
        socket.on("updateSoftware", (data) => processData( data ) );
        socket.on("job_status", (data) => jobStatus(data) );
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
</body>
</html>
