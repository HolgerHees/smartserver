<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/","/system_service/"]); ?>
<script>
mx.UNCore = (function( ret ) {
    let type = null
    let reverse = null;
    let observed_ips = null;

    function cleanTime(time)
    {
        return time.substring(0,time.length - 3);
    }

    function formatDate(date)
    {
        if( date )
        {
            if( date.toLocaleDateString() == (new Date()).toLocaleDateString() )
            {
                return [ mx.I18N.get("Today, {}").fill(cleanTime(date.toLocaleTimeString())), "today" ];
            }
            else if( date.toLocaleDateString() == ( new Date(new Date().getTime() - 24*60*60*1000) ).toLocaleDateString() )
            {
                return [ mx.I18N.get("Yesterday, {}").fill(cleanTime(date.toLocaleTimeString())), "yesterday" ];
            }
            else
            {
                return [ cleanTime(date.toLocaleString()), "other" ];
            }
        }
        else
        {
            return [ null, null ];
        }
    }

    function formatTimestamp(timestamp)
    {
        let result = formatDate(new Date(timestamp*1000));
        return result[0];
    }

    function convertIP(ip)
    {
        return ip.split('.')
            .map(p => parseInt(p))
            .reverse()
            .reduce((acc,val,i) => acc+(val*(256**i)),0)
    }

    function compareIP(reverse, ip1,ip2)
    {
        if( ip1 == null ) ip1 = "0";
        if( ip2 == null ) ip2 = "0";

        return ( reverse ? convertIP(ip1) < convertIP(ip2) : convertIP(ip1) > convertIP(ip2) ) ? 1 : -1;
    }

    function isSearchMatch(searchTerm, data)
    {
        return false;
    }

    function buildTable(searchTerm, _type, _reverse, _data)
    {
        type = _type;
        reverse = _reverse;
        observed_ips = _data;

        observed_ips.sort(function(first, second) {
            if( type == "ip" )
                return compareIP(reverse, first[type], second[type]);
            else
                return ( reverse ? first[type] < second[type] : first[type] > second[type] ) ? 1 : -1;
        });

        let rows = [];
        observed_ips.forEach(function(data)
        {
            if( searchTerm && !isSearchMatch(searchTerm, data) )
                return;

            //console.log(data);

            actions = [];
            if( data["state"] != 'approved' ) actions.push('<div style="padding: 5px 12px;" class="form button" onclick="mx.UNCore.trigger(\'approveObservedIP\',\'' + data["ip"] + '\')" data-tooltip=\'Approve\'>A</div>');
            if( data["state"] != 'unblocked' ) actions.push('<div style="padding: 5px 12px;" class="form button" onclick="mx.UNCore.trigger(\'unblockObservedIP\',\'' + data["ip"] + '\')" data-tooltip=\'Unblock\'>U</div>');
            if( data["state"] != 'blocked' ) actions.push('<div style="padding: 5px 12px;" class="form button" onclick="mx.UNCore.trigger(\'blockObservedIP\',\'' + data["ip"] + '\')" data-tooltip=\'Block\'>B</div>');
            actions.push('<div class="form button" onclick="mx.UNCore.trigger(\'removeObservedIP\',\'' + data["ip"] + '\')" data-tooltip=\'Remove\'>R</div>');

            rows.push({
                "events": {
                    "click": function(event){
                        event.stopPropagation();
                    }
                },
                "columns": [
                    { "value": formatTimestamp(data["last"]) },
                    { "value": data["ip"] },
                    { "value": data["count"] },
                    { "value": data["group"] },
                    { "value": data["state"], 'class': "state " + data["state"] },
                    { "value": data["reason"] },
                    { "value": data["blocklist"] },
                    { "value": formatTimestamp(data["created"]) },
                    { "value": formatTimestamp(data["updated"]) },
                    { "value": actions.join('') }
                ]
            });
        });

        let table = mx.Table.init( {
            "class": "list",
            "sort": { "value": type, "reverse": reverse, "callback": function(_type,_reverse){ buildTable(searchTerm, _type, type != _type ? reverse : _reverse, observed_ips) } },
            "header": [
                { "value": "Last", "sort": { "value": "last", "reverse": true } },
                { "value": "IP", "sort": { "value": "ip", "reverse": true } },
                { "value": "Count", "sort": { "value": "count", "reverse": true } },
                { "value": "Group", "sort": { "value": "group", "reverse": true } },
                { "value": "State", "sort": { "value": "state", "reverse": true } },
                { "value": "Reason", "sort": { "value": "reason", "reverse": true } },
                { "value": "Blocklist", "sort": { "value": "blocklist", "reverse": true } },
                { "value": "Created", "sort": { "value": "created", "reverse": true } },
                { "value": "Updated", "sort": { "value": "updated", "reverse": true } },
                { "value": "Actions" }
            ],
            "rows": rows
        });

        table.build(mx.$("#ipList"));

        mx.Tooltip.init();
    }

    ret.trigger = function(action, ip){
        socket.emit(action, {'ip': ip});
    }

    ret.processData = function(data){

        buildTable("", 'last', true, data);
    }

    ret.init = function()
    { 
        mx.I18N.process(document);
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );

var processData = mx.OnDocReadyWrapper( mx.UNCore.processData );

mx.OnSharedModWebsocketReady.push(function(){
    socket = mx.ServiceSocket.init('system_service', 'observed_ips');
    socket.on("data", (data) => processData(data));
});
</script>
<style>
.form .button {
    margin-right: 5px;
    padding: 5px 12px;
    display: inline-block;
}
.form .button:last-child {
    margin-right: 0px;
}

#ipList .state.approved {
    color: var(--dark-color-blue);
}
#ipList .state.blocked {
    color: var(--dark-color-red);
}
#ipList .state.unblocked {
    color: var(--dark-color-green);
}
</style>
</head>
<body class="inline">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Observed IP's")); } );</script>

<div id="ipList"></div>
</body>
</html>
