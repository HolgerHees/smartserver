<?php
require "../shared/libs/ressources.php";

require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link rel="stylesheet" href="/shared/css/logfile/logfile_box.css">
<link rel="stylesheet" href="./css/core.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="/shared/js/logfile/logfile.js"></script>
<script src="./js/core.js"></script>
<script>
function initPage()
{
    var daemonApiUrl = mx.Host.getBase() + 'api/'; 
    var refreshDaemonStateTimer = null;
    
    function processData(last_data_modified, changed_data)
    {
        if( changed_data.hasOwnProperty("jobs") )
        {
            changed_data["jobs"].sort(function(a,b){ return a["timestamp"] == b["timestamp"] ? 0 : ( a["timestamp"] < b["timestamp"] ? 1 : -1 ); });
            
            let rows = [];
            changed_data["jobs"].forEach(function(job)
            {
                let date = new Date(job["timestamp"] * 1000);
                
                rows.push({
                    "onclick": function(){ mx.CICore.openDetails(event,job['date'],job['config'],job['deployment'],job['branch'],job['git_hash']); },
                    "data": { "timestamp": job["timestamp"] },
                    "columns": [
                        { "class": "state " + job['state'] },
                        { "value": "<span class=\"icon-down branch\">" + job['branch'] + "</span><span class=\"username\">" + job['author'] + "<span>" },
                        { "value": "<div>" + job['subject'] + "</div>", "class": "subject" },
                        { "value": job['config'] },
                        { "value": job['deployment'] },
                        { "value": mx.Logfile.formatState(job['state']) + "<span class=\"hash icon-resize-horizontal\" onClick=\"mx.CICore.openGitCommit(event,\'https://github.com/HolgerHees/smartserver/commit/" + job['git_hash'] + "\');\"><span>" + job['git_hash'].substr(0,7) + "</span><span class=\"icon-export\"></span></span>" },
                        { "value": "<span class=\"runtime icon-clock\">" + mx.Logfile.formatDuration(job['duration']) + "</span><span class=\"datetime icon-calendar-empty\">" + date.toLocaleString() + "</span>" }
                    ]
                });
            });

            let table = mx.Table.init( {
                "class": "logfileBox",
                "header": [],
                "rows": rows
            });
            
            let tableElement = mx.$("#jobs");
            
            table.build(tableElement);
            
            let runningElements = mx.$$("#jobs div.state.running");
            runningElements.forEach(function(element)
            {
                let startTimestamp = element.parentNode.dataset.timestamp;
                let runtimeElement = element.parentNode.querySelector(".runtime");
                
                function counter()
                {
                    if( !element.isConnected ) return;
                    let duration = Math.round( ( Date.now() / 1000 ) - startTimestamp );
                        
                    runtimeElement.innerHTML = mx.Logfile.formatDuration(duration);
                    window.setTimeout(counter,1000);
                }
                counter();
            });
        }
    }
    
    function handleDaemonState(state)
    {
        window.clearTimeout(refreshDaemonStateTimer);
        
        if( Object.keys(state["changed_data"]).length > 0 ) processData(state["last_data_modified"], state["changed_data"]);
        
        refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
    }
    
    function refreshDaemonState(last_data_modified, callback)
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
                handleDaemonState(response);
                
                if( callback ) callback();
            }
            else
            {
                let timeout = 15000;
                refreshDaemonStateTimer = mx.Page.handleRequestError(this.status,daemonApiUrl,function(){ refreshDaemonState(last_data_modified, callback) }, timeout);
            }
        };
        
        xhr.send(mx.Core.encodeDict( { "last_data_modified": last_data_modified } ));
    }
    
    refreshDaemonState(null, function(){
        //console.log("init");
    });
        
    //mx.CIList.init(mx.$$('div.row'),mx.$("div.table"), 'div.state', 'span.state','span.runtime');
    //mx.CIList.startUpdateProcess();
    mx.Page.refreshUI();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer-800", "CI Service"); } );</script>
<div id="jobs">
</div>
</body>
</html>
