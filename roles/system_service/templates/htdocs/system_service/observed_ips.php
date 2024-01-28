<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/system_service/"]); ?>
<script>
mx.UNCore = (function( ret ) {
    var daemonApiUrl = mx.Host.getBase() + '../api/';
    var refreshDaemonStateTimer = 0;

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
                    { "value": data["state"] },
                    { "value": data["reason"] },
                    { "value": data["blocklist"] },
                    { "value": formatTimestamp(data["created"]) },
                    { "value": formatTimestamp(data["updated"]) }
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
                { "value": "Updated", "sort": { "value": "updated", "reverse": true } }
            ],
            "rows": rows
        });

        table.build(mx.$("#ipList"));
    }

    function handleIPList(result)
    {
        window.clearTimeout(refreshDaemonStateTimer);

        buildTable("", 'last', true, result["changed_data"]["observed_ips"]);

        //console.log(state);

        refreshDaemonStateTimer = window.setTimeout(function(){ refreshIPListe(state["last_data_modified"], null) }, 60000);
    }

    function refreshIPListe(last_data_modified,callback)
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl + "observed_ips/" );
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

        //application/x-www-form-urlencoded

        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;

            if( this.status == 200 )
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    mx.Error.confirmSuccess();

                    handleIPList(response);

                    if( callback ) callback();
                }
                else
                {
                    mx.Error.handleServerError(response["message"])
                }
            }
            else
            {
                if( this.status == 0 || this.status == 503 )
                {
                    mx.Error.handleError( mx.I18N.get( mx.UpdateServiceHelper.isRestarting() ? "Service is restarting" : "Service is currently not available")  );
                }
                else
                {
                    if( this.status != 401 ) mx.Error.handleRequestError(this.status, this.statusText, this.response);
                }

                refreshDaemonStateTimer = mx.Page.handleRequestError(this.status,daemonApiUrl,function(){ refreshDaemonState(last_data_modified, callback) }, 60000);
            }
        };

        xhr.send(mx.Core.encodeDict( { "last_data_modified": last_data_modified } ));
    }

    ret.init = function()
    { 
        mx.I18N.process(document);
        
        refreshIPListe()
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );
</script>
</head>
<body class="inline">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Observed IP's")); } );</script>

<div id="ipList"></div>
</body>
</html>
