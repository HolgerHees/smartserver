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
            
        if( groupsChanged || devicesChanged || statsChanged )
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
                    mx.Error.handleServerNotAvailable( mx.I18N.get( "Service is currently not available") );
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
<style>
body, svg {
    width: 100%;
    height: 100%;
}
.tooltip {
    background: #fff;
    pointer-events: auto;
}
.tooltip span.text > div,
.tooltip div.rows > div {
    display: table;
}
.tooltip span.text > div > div,
.tooltip div.rows > div > div {
    display: table-row;
}
.tooltip span.text > div > div > div,
.tooltip div.rows > div > div > div {
    display: table-cell;
    padding: 3px;
    text-align: left;
}
.tooltip span.text > div > div > div:first-child {
    font-weight: bold;
}
.tooltip div.rows {
    padding: 0 !important;
}

@keyframes traffic_arrived {
  from {
     fill: #111;
  }
  to {
     fill: #b5ce69;
  }
}

svg g.links {
    fill: none;
    stroke-width: 1;
    stroke: var(--content-text);
}
svg g.links path.online,
svg g.links path.offline {
    stroke-width: 2;
}

svg g.links path.online {
    stroke: var(--color-green);
}
svg g.links path.offline {
    stroke: var(--color-red);
}

svg g.nodes rect.container {
    stroke-width: 0.5;
    stroke: var(--content-text);
    fill: #fff;
}

svg g.nodes rect.container.network {
    fill: #d2e2ef;
}

svg g.nodes circle.online,
svg g.nodes circle.offline {
    stroke-width: 0.5;
    stroke: var(--content-text);
}
svg g.nodes circle.online {
    fill: var(--color-green);
}
svg g.nodes circle.offline {
    fill: var(--color-red);
}

svg g.nodes rect.traffic {
    fill: white;
}

svg g.nodes text.name,
svg g.nodes text.details {
    fill: #777;
    font-weight: 300;
}
svg g.nodes text.details tspan.hs {
    font-weight: 500;
}

svg g.nodes text.traffic.arrived {
    animation-name: traffic_arrived;
    animation-duration: 0.5s;
    animation-direction: alternate;
    animation-iteration-count: 5;
}
/*.tooltip div.services > div > div > div:first-child {
    text-align: right;
}*/
</style>
<div class="error"></div>
<div id="tooltip"></div>
<svg id="network"></svg>
</body>
</html>
