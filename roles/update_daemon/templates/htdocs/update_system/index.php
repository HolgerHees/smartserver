<?php
require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="./css/shared.css">
<link rel="stylesheet" href="./css/index.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
<script>
function initPage()
{
    var element = mx.$("#systemProcesses");
    if( element )
    {
        window.setTimeout(function(){ mx.$("#systemProcesses").click(); }, 100 );
    }
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>
    var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
    if( theme ) document.body.classList.add(theme);
    
    mx.UNCore = (function( ret ) {
        function callResultCheck(callback)
        {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", mx.Host.getBase() + 'api.php' );
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    if( !this.response )
                    {
                        window.setTimeout(function(){ callResultCheck(callback); },1000);
                    }
                    else
                    {
                        var response = JSON.parse(this.response);
                        if( response.returncode == "0" )
                        {
                            if( response.need_refresh )
                            {
                                callApi({'action': "refreshUpdateState", "parameter": response.need_refresh },function(){
                                    location.reload();
                                });
                            }
                            else
                            {
                                callback(response.result);
                            }
                        }
                        else
                        {
                            callback("daemon error");
                        }
                    }
                }
                else
                {
                    callback("result error");
                }
            };
            xhr.send(JSON.stringify({"action": "result"}));
        }
      
        function callApi(parameter,callback)
        {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", mx.Host.getBase() + 'api.php' );
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    if( this.response == "1" ) callResultCheck(callback);
                    else callback("another job is still running");
                }
                else
                {
                    callback("trigger error");
                }
            };
            xhr.send(JSON.stringify(parameter));
        }
        
        ret.toggle = function(btn,id)
        {
            var element = mx.$("#"+id);
            if( element.style.maxHeight )
            {
                element.style.maxHeight = "";
                window.setTimeout(function(){ element.style.display=""; btn.innerText="Show"; },300);
            }
            else
            {
                element.style.display = "block";
                window.setTimeout(function(){ element.style.maxHeight = ( element.scrollHeight + 20 ) + "px"; btn.innerText="Hide"; },0);
                
            }
        }
        
        ret.action = function(btn, action, parameter )
        {
            if( btn.classList.contains("disabled") ) 
            {
                return;
            }
            
            btn.classList.add("disabled");
            
            callApi({'action': action, 'parameter': parameter}, function(data){
                btn.classList.remove("disabled");
                alert(data);
            });
        }
        return ret;
    })( mx.UNCore || {} );
</script>
<?php
    if( file_exists($system_state_file) )
    {
        $data = file_get_contents($system_state_file);
        $data = json_decode($data);
    }
    else
    {
        $data = array();
    }
   
#    echo "Deployment state " . $data->smartserver_code . "<br>";
#    echo "Deployment has " . count($data->smartserver_changes) . " updates<br>";
#{"repository": "Update repository with updates from SUSE Linux Enterprise 15", "name": "shared-mime-info-lang  ", "current": "1.12-1.26                      ", "update": "1.12-3.3.1                     ", "arch": "noarch"}

    $needs_system_reboot = false;
    $service_restarts = [];
    foreach( $data->os_outdated as $outdate)
    {
        if( empty($outdate->service) ) $needs_system_reboot = true;
        else $service_restarts[] = $outdate->service;
    }
?>
<div class="widget">
<?php
    echo "<h1>System status</h1>";
    if( $data->os_reboot || $needs_system_reboot )
    { 
        echo "<div class=\"action\"><div class=\"info red\">Reboot needed (";
        $reason = [];
        if( $data->os_reboot ) $reason[] = "installed core updates";
        if( $needs_system_reboot ) $reason[] = "outdated processes";
        echo implode(", ", $reason);
        echo ")</div><div class=\"buttons\"><div class=\"button red\" onclick=\"mx.UNCore.action(this,'systemReboot')\">Reboot system</div></div></div>";
    }
    if( count($data->os_outdated) > 0 )
    {
?>
<div class="action"><div class="info">System has <?php echo count($data->os_outdated); ?> outdated processes</div><div class="buttons"><?php if(count($service_restarts)>0) echo "<div class=\"button yellow\" onclick=\"mx.UNCore.action(this,'restartService','" . implode(",",$service_restarts) . "')\">Restart services</div>"; ?><div class="button" id="systemProcesses" onclick="mx.UNCore.toggle(this,'outdated')">Show</div></div></div>
<div class="table" id="outdated">
  <div class="row">
    <div>PID</div>
    <div>PPID</div>
    <div>UID</div>
    <div>User</div>
    <div class="grow">Command</div>
    <div class="grow">Service</div>
    <div></div>
  </div>
<?php
foreach( $data->os_outdated as $outdate)
{
    echo "<div class=\"row\">";
    echo "<div>" . $outdate->pid . "</div>";
    echo "<div>" . $outdate->ppid . "</div>";
    echo "<div>" . $outdate->uid . "</div>";
    echo "<div>" . $outdate->user . "</div>";
    echo "<div>" . $outdate->command . "</div>";
    echo "<div>" . $outdate->service . "</div>";
    echo "<div>" . ( $outdate->service ? "<div class=\"button yellow\" onclick=\"mx.UNCore.action(this,'restartService','" . $outdate->service . "')\">Restart</div>" : "" ) . "</div>";
    echo "</div>";
}
?>
</div>
<?php
    }
    else
    {
        echo "<div class=\"action\"><div class=\"info green\">No outdates processes</div></div>";
    }
?>
</div>

<div class="widget">
<h1>Updates</h1>
<?php 
    if( count($data->os_updates) > 0 )
    {
?>
<div class="action"><div class="info"><?php echo count($data->os_updates); ?> System updates</div><div class="buttons"><div class="button red" onclick="mx.UNCore.action(this,'installSystemUpdates')">Install updates</div><div class="button" onclick="mx.UNCore.toggle(this,'system_updates')">Show</div></div></div>
<div class="table" id="system_updates">
  <div class="row">
    <div>Name</div>
    <div>Current</div>
    <div class="grow">Update</div>
    <div>Arch</div>
  </div>
<?php
foreach( $data->os_updates as $update)
{
    echo "<div class=\"row\">";
    echo "<div>" . $update->name . "</div>";
    echo "<div>" . $update->current . "</div>";
    echo "<div>" . $update->update . "</div>";
    echo "<div>" . $update->arch . "</div>";
    echo "</div>";
}
?>
</div>
<?php 
    }
    else
    {
        echo "<div class=\"action\"><div class=\"info green\">No system updates available</div></div>";
    }
    if( count($data->smartserver_changes) > 0 )
    {
?>
<div class="action"><div class="info"><?php echo count($data->smartserver_changes); ?> Deployment updates</div><div class="buttons"><div class="button red" onclick="mx.UNCore.action(this,'deploySmartserverUpdates')">Deploy updates</div><div class="button" onclick="mx.UNCore.toggle(this,'deployment_updates')">Show</div></div></div>
<div class="table" id="deployment_updates">
  <div class="row">
    <div>Flag</div>
    <div class="grow">File</div>
  </div>
<?php
foreach( $data->smartserver_changes as $update)
{
    echo "<div class=\"row\">";
    echo "<div>" . $update->flag . "</div>";
    echo "<div>" . $update->path . "</div>";
    echo "</div>";
}
?>
</div>
<?php 
    }
    else
    {
        echo "<div class=\"action\"><div class=\"info green\">No deployment updates available</div></div>";
    }
?>
</div>
</body>
</html>
