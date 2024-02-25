<?php
require "../shared/libs/ressources.php";
?>
<html style="background-color: transparent !important;">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/","/system_service/"]); ?>
<script>
mx.UNCore = (function( ret ) {
    ret.processData = function(data)
    {
        let btn = mx.$(".speedtest.button");
        if( data["is_running"] )
        {
            btn.classList.add("disabled");
            btn.innerHTML = '<span style="margin-right: 25px;">' + mx.I18N.get("Speedtest active") + '</span><span style="position: absolute;top:4px;right: 15px;"><svg style="width: 35px; height: 35px; color:black;" x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve"><use href="#progress" /></svg></span>';
        }
        else
        {
            if( btn.classList.contains("disabled") ) window.parent.postMessage({ type: 'grafana', content: "reload" }, "*");

            btn.classList.remove("disabled")
            btn.innerText = mx.I18N.get("Start speedtest");
        }
    }

    ret.init = function()
    { 
        mx.I18N.process(document);
    }

    ret.trigger = function()
    {
        if( mx.$(".speedtest.button").classList.contains("disabled") ) return;

        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", "/system_service/api/triggerSpeedtest/", false );
        xmlHttp.send( null );
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );

var processData = mx.OnDocReadyWrapper( mx.UNCore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    let socket = mx.ServiceSocket.init('system_service', "speedtest");
    socket.on("data", (data) => processData(data));
});
</script>
</head>
<body class="inline" style="background-color: transparent !important;">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Network speedtest")); } );</script>
<div style="display:flex;align-items:center;justify-content:center;height:100%;">
  <div class="speedtest form button" onclick="mx.UNCore.trigger()"></div>
</div>
<span style="display:none">
    <svg id="progress" x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve">
        <path fill="currentColor" d="M73,50c0-12.7-10.3-23-23-23S27,37.3,27,50 M30.9,50c0-10.5,8.5-19.1,19.1-19.1S69.1,39.5,69.1,50">
            <animateTransform attributeName="transform" attributeType="XML" type="rotate" dur="1s" from="0 50 50" to="360 50 50" repeatCount="indefinite"></animateTransform>
        </path>
    </svg>
</span>
</body>
</html>
