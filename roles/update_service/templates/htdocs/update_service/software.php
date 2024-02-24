<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/update_service/"]); ?>
<script>
mx.SNCore = (function( ret ) {
    ret.socket = null;

    var jobtimer = null;

    function setLoadingGear(data)
    {
        mx.SoftwareVersionsTemplates.setLoadingGear(data);
        jobtimer = window.setTimeout(function(){ setLoadingGear(data); }, 1000);
    }

    ret.startSoftwareCheck = function()
    {
        mx.SNCore.socket.emit("refreshSoftwareVersionCheck");
    }

    ret.processData = function(data)
    {
        if( "job_status" in data && data["job_status"]["job"] == "software_check" )
        {
            setLoadingGear(data["job_status"]["started"]);
            return;
        }
        else if( jobtimer )
        {
            window.clearTimeout(jobtimer);
        }

        if( "software_versions" in data )
        {
            mx.SoftwareVersionsTemplates.processData(data["software_versions"])
            mx.Page.refreshUI();
        }
    }

    ret.openUrl = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }
    
    return ret;
})( mx.SNCore || {} );
    
var processData = mx.OnDocReadyWrapper( mx.SNCore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    mx.SNCore.socket = mx.ServiceSocket.init('update_service', 'software');
    mx.SNCore.socket.on("data", (data) => processData( data ) );
});
</script>
</head>
<body class="software">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer-800", mx.I18N.get("Software")); } );</script>
<div class="list"></div>
</body>
</html>
