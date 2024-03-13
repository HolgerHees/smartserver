<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/shared/mod/logfile/", "/update_service/"]); ?>
<script>
mx.CICore = (function( ret ) {
    const params = new URLSearchParams(window.location.search);
    ret.log_datetime = params.get("datetime");
    ret.log_cmd = params.get("cmd");
    ret.log_username = params.get("username");

    var initialized = false;
    var header = null;

    var logContainer = null;
    var scrollControl = null;
    var goToControl = null;
    var runtimeControl = null;

    var stateColorElement = null;
    var stateTextElement = null;

    ret.socket = null;

    ret.processData = function(data)
    {
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

                    mx.$('div.cmd',header).innerHTML = data["job"]["cmd"];
                    mx.$('div.username',header).innerHTML = data["job"]["username"];

                    let startTime = new Date(data["job"]["timestamp"] * 1000);

                    mx.Logfile.initData(startTime, data["job"]["duration"], data["log"] )

                    mx.$('div > span.datetime',header).innerHTML = startTime.toLocaleString();

                    mx.Page.refreshUI();
                }
                initialized = true;
            }
        }

        mx.Page.refreshUI();
    }

    ret.openOverview = function(event)
    {
        document.location = '../system/';
    }

    ret.init = function()
    {
        header = mx.$('div.header > div.row');

        logContainer = mx.$('div.log');
        scrollControl = document.querySelector('div.scrollControl');
        goToControl = document.querySelector('div.goToControl');
        runtimeControl = mx.$('div > span.runtime',header);

        stateColorElement = mx.$('div.state',header);
        stateTextElement = mx.$('div.statetext > span.state',header);

        mx.Logfile.init(logContainer, scrollControl, goToControl, runtimeControl);
    }

    return ret;
})( mx.CICore || {} );

mx.OnDocReady.push(mx.CICore.init);

var processData = mx.OnDocReadyWrapper( mx.CICore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    mx.CICore.socket = mx.ServiceSocket.init('update_service', 'update_details', function(){ return { "datetime": mx.CICore.log_datetime, "cmd": mx.CICore.log_cmd, "username": mx.CICore.log_username} } );
    mx.CICore.socket.on("data", (data) => processData( data ) );
});
</script>
</head>
<body>
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame(null, mx.I18N.get("Job details") + mx.CICore.log_cmd); } );</script>
<div class ="header form table logfileBox">
    <div class="row" onClick="mx.CICore.openOverview(event)">
        <div class="state"></div>
        <div class="cmd" ></div>
        <div class="username" ></div>
        <div class="statetext"><span class="state"></span></div>
        <div><span class="runtime icon-clock"></span><span class="datetime icon-calendar-empty"></span></div>
    </div>
</div>
<div class="scrollControl" onClick="mx.Logfile.toggleBottomScroll()"></div><div class="goToControl"><div></div></div>
<div class="logContainer"><div class="log"></div></div>
<?php
/*    echo '<div class ="header form table logfileBox">
    
    <div id="' . $job->getHash() . '" data-state="' . $job->getState() . '" data-duration="' . $job->getDuration() . '" class="row" onClick="mx.CICore.openOverview(event)">
    <div class="state ' . $job->getState() . '"></div>
    
    <div class="cmd" >' . $job->getCmd() . '</div>
    <div class="username" >' . $job->getUsername() . '</div>

    <div>' . LogFile::formatState($job->getState()) . '</div>
    
    <div><span class="runtime icon-clock">' . explode(".",LogFile::formatDuration($job->getDuration()))[0] . '</span><span class="datetime icon-calendar-empty">' . $job->getDateTime()->format('d.m.Y H:i:s') . '</span></div>
    </div>

    </div><div class="scrollControl" onClick="mx.Logfile.toggleBottomScroll()"></div><div class="goToControl"><div></div></div>';

    echo '<div class="logContainer"><div class="log">';
    
    foreach( $logfile->getLines() as $line )
    {
        echo LogFile::getLogLine($line);
    }
    
    echo '</div></div>';*/
?>
</body>
</html>
