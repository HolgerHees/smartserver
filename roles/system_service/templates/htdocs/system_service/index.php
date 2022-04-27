<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link href="<?php echo Ressources::getCSSPath('/system_service/'); ?>" rel="stylesheet">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/system_service/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/system_service/'); ?>"></script>
<script src="https://d3js.org/d3.v7.js"></script>
<script>
mx.UNCore = (function( ret ) {
    var daemonApiUrl = mx.Host.getBase() + 'api/'; 
    
    var refreshDaemonStateTimer = 0;
    var groups = [];    
    var devices = [];    
    var stats = {};    
    var root_device_mac = null;
    
    function handleDaemonState(state)
    {
        window.clearTimeout(refreshDaemonStateTimer);
        
        let groupsChanged = false;
        let devicesChanged = false;
        let statsChanged = false;
        
        if( state["changed_data"].hasOwnProperty("groups") )
        {
            groups = state["changed_data"]["groups"];
            groupsChanged = true;
        }
        
        if( state["changed_data"].hasOwnProperty("devices") )
        {
            root_device_mac = state["changed_data"]["root"];
            devices = state["changed_data"]["devices"];
            devices = devices.sort(function(a, b)
            {
                if( a.ip == null ) return -1;
                if( b.ip == null ) return 1;
                
                if( a.ip.length > b.ip.length ) return 1;
                if( a.ip.length < b.ip.length ) return -1;
                
                return a.ip > b.ip;
            });
            devicesChanged = true;
        }
        
        if( state["changed_data"].hasOwnProperty("stats") )
        {
            let _stats = {}
            
            state["changed_data"]["stats"].forEach(function(stat)
            {
                key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"]
                _stats[key] = stat;
            });
            
            //console.log(_stats)
            stats = _stats;
            statsChanged = true;
        }
        
        if( devices.length == 0 )
        {
            mx.Error.handleError( mx.I18N.get("Network analysis is in progress")  );
        }
        else if( groupsChanged || devicesChanged || statsChanged )
        {
            mx.D3.drawCircles( root_device_mac, groupsChanged || devicesChanged ? devices : null, groupsChanged || devicesChanged ? groups : null, statsChanged || devicesChanged ? stats : null , 15000);
        }

        refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
             
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
                
                refreshDaemonStateTimer = mx.Page.handleRequestError(this.status,daemonApiUrl,function(){ refreshDaemonState(last_data_modified, callback) }, 15000);
            }
        };
        
        xhr.send(mx.Core.encodeDict( { "last_data_modified": last_data_modified } ));
    }
        
    ret.init = function()
    { 
        mx.D3.init();
        
        mx.I18N.process(document);
        
        refreshDaemonState(null, function(state){});
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );
</script>
</head>
<body class="inline">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Network visualizer")); } );</script>
<div class="error"></div>
<svg id="network"></svg>
</body>
</html>
