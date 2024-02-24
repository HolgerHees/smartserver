<?php
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/shared/mod/logfile/"]); ?>

<link rel="stylesheet" href="../css/core.css">
<script src="../js/core.js"></script>
<script>
mx.CICore = (function( ret ) {
    const params = new URLSearchParams(window.location.search);
    ret.log_datetime = params.get("datetime");
    ret.log_config = params.get("config");
    ret.log_os = params.get("os");
    ret.log_branch = params.get("branch");
    ret.log_hash = params.get("hash");

    var initialized = false;
    var header = null;

    var logContainer = null;
    var scrollControl = null;
    var goToControl = null;
    var runtimeControl = null;

    var stateColorElement = null;
    var stateTextElement = null;

    ret.socket = null;

    ret.processData = function(data){

        if( data["logline"] )
        {
            let div = document.createElement("div");
            div.innerHTML = data["logline"];
            let clone = div.firstChild.cloneNode(true);
            logContainer.appendChild(clone);

            mx.Logfile.triggerUpdate();
        }
        else
        {
            if( data["error"] )
            {
                mx.Error.handleError(data["error"]);
            }
            else
            {
                //header.dataset.duration = data["job"]["duration"];
                runtimeControl.dataset.state = data["job"]["state"];

                stateColorElement.className="state " + data["job"]["state"];
                stateTextElement.className="state " + data["job"]["state"];
                stateTextElement.innerHTML = mx.Logfile.formatState(data["job"]["state"]);

                if( !initialized )
                {
                    if( data["topic"] )
                    {
                        mx.CICore.socket.emit('join',data["topic"]);
                        mx.CICore.socket.on("data", (data) => processData( data ), data["topic"] );
                    }

                    mx.$('span.branch',header).innerHTML = data["job"]["branch"];
                    mx.$('span.username',header).innerHTML = data["job"]["author"];
                    mx.$('div.subject div',header).innerHTML = data["job"]["subject"];
                    mx.$('div.config',header).innerHTML = data["job"]["config"];
                    mx.$('div.deployment',header).innerHTML = data["job"]["deployment"];

                    mx.$('div.gitlink > span.hash',header).onclick = function(){ mx.CICore.openGitCommit(event,'https://github.com/HolgerHees/smartserver/commit/' + data["job"]["git_hash"] ); };
                    mx.$('div.gitlink > span.hash > span',header).innerHTML = data["job"]["git_hash"].substring(0,7);

                    let startTime = new Date(data["job"]["timestamp"] * 1000);

                    mx.Logfile.initData(startTime, data["job"]["duration"], data["log"] )

                    mx.$('div > span.datetime',header).innerHTML = startTime.toLocaleString();

                    mx.Page.refreshUI();
                }
                initialized = true;
            }
        }
    };

    ret.init = function(){
        header = mx.$('div.header > div.row');

        logContainer = mx.$('div.log');
        scrollControl = document.querySelector('div.scrollControl');
        goToControl = document.querySelector('div.goToControl');
        runtimeControl = mx.$('div > span.runtime',header);

        stateColorElement = mx.$('div.state',header);
        stateTextElement = mx.$('div.gitlink > span.state',header);

        mx.Logfile.init(logContainer, scrollControl, goToControl, runtimeControl);
    };

    return ret;
})( mx.CICore || {} );

mx.OnDocReady.push(mx.CICore.init);

var processData = mx.OnDocReadyWrapper( mx.CICore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    mx.CICore.socket = mx.ServiceSocket.init('ci_service', "details", function(){ return { "datetime": mx.CICore.log_datetime, "config": mx.CICore.log_config, "os": mx.CICore.log_os, "branch": mx.CICore.log_branch, "hash": mx.CICore.log_hash} } );
    mx.CICore.socket.on("data", (data) => processData( data ) );
});
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, "CI Test - " + mx.CICore.log_config + "-" + mx.CICore.log_os + "-" + mx.CICore.log_branch); } );</script>
<div class ="header form table logfileBox">
    <div class="row" onClick="mx.CICore.openOverview(event)">
        <div class="state"></div>
        <div><span class="icon-down branch"></span><span class="username"><span></div>
        <div class="subject"><div></div></div>
        <div class="config"></div>
        <div class="deployment"></div>
        <div class="gitlink"><span class="state"></span><span class="hash icon-resize-horizontal" onClick=""><span></span><span class="icon-export"></span></span></div>
        <div><span class="runtime icon-clock"></span><span class="datetime icon-calendar-empty"></span></div>
    </div>
</div>
<div class="scrollControl" onClick="mx.Logfile.toggleBottomScroll()"></div><div class="goToControl"><div></div></div>
<div class="logContainer"><div class="log"></div></div>
</body>
</html>
