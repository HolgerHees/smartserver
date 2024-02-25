<?php
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/shared/mod/logfile/","/ci_service/"]); ?>
<script>
var processData = mx.OnDocReadyWrapper(function(data){
    if( "jobs" in data )
    {
        data["jobs"].sort(function(a,b){ return a["timestamp"] == b["timestamp"] ? 0 : ( a["timestamp"] < b["timestamp"] ? 1 : -1 ); });

        let rows = [];
        data["jobs"].forEach(function(job)
        {
            let date = new Date(job["timestamp"] * 1000);

            rows.push({
                "events": { "click": function(){ mx.CICore.openDetails(event,job['date'],job['config'],job['deployment'],job['branch'],job['git_hash']); } },
                "data": { "timestamp": job["timestamp"] },
                "columns": [
                    { "class": "state " + job['state'] },
                    { "value": "<span class=\"icon-down branch\">" + job['branch'] + "</span><span class=\"username\">" + job['author'] + "<span>" },
                    { "value": "<div>" + job['subject'] + "</div>", "class": "subject" },
                    { "value": job['config'] },
                    { "value": job['deployment'] },
                    { "value": '<span class="state ' + job['state'] + '">' + mx.Logfile.formatState(job['state']) + "</span><span class=\"hash icon-resize-horizontal\" onClick=\"mx.CICore.openGitCommit(event,\'https://github.com/HolgerHees/smartserver/commit/" + job['git_hash'] + "\');\"><span>" + job['git_hash'].substr(0,7) + "</span><span class=\"icon-export\"></span></span>" },
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
    mx.Page.refreshUI();
});

mx.OnSharedModWebsocketReady.push(function(){
    let socket = mx.ServiceSocket.init('ci_service', "overview");
    socket.on("data", (data) => processData( data ) );
});
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer-800", "CI Service"); } );</script>
<div id="jobs"></div>
</body>
</html>
