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
    var groups = {};    
    var devices = {};    
    var stats = {};    
    var root_device_mac = null;
    
    var nodes = {};
    
    var rootNode = null;
    
    var isTable = false;
    var activeTerm = "";

    var demo_ip_map = {};
    var demo_mac_map = {};

    function getDeviceSignal(device)
    {
        let group = null;
        let stat = null;
        
        device.groups.forEach(function(_group)
        {
            if( group == null || group.details.priority["value"] < _group.details.priority["value"] )
            {
                group = _group;
            }
        });

        if( group != null )
        {
            let _stat = device.interfaceStat.data.filter(data => data["connection_details"]["gid"] == group.gid);
            if( _stat.length > 0)
            {
                stat = _stat[0];
            }
            else
            {
                console.log("----");
                console.log(device.groups);
                console.log(device.interfaceStat);
                console.log(group);
                console.log(stats);
            }
        }
        
        if( group && stat && stat.details["signal"] )
        {    
            return { "group": group, "stat": stat }
        }
        
        return null;
    }

    function getGroup(gid)
    {
        return groups[gid];
    }
    
    function getDeviceStat(device)
    {
        return stats.hasOwnProperty(device["mac"]) ? stats[device["mac"]] : null;
    }

    function getInterfaceStat(device)
    {
        if( device["connection"] )
        {
            key = device["connection"]["target_mac"] + ":" + device["connection"]["target_interface"];
            if( stats.hasOwnProperty(key) ) return stats[key];
        }
        return null;
    }

    function isOnline(device)
    {
        if( device.type == 'hub' )
        {
            let all_children_online = true;
            for(let child_device of device.connected_from) 
            {
                let child_device_stat = getDeviceStat(child_device);
                if( !child_device_stat || child_device_stat.offline_since != null )
                {
                    all_children_online = false;
                    break;
                }
            }
            return all_children_online;
        }

        let device_stat = getDeviceStat(device);
        return device_stat && device_stat.offline_since == null;
    }

    function initNode(device)
    {
        let node = {};
        node["name"] = device["mac"];
        node["device"] = device;
        node["children"] = [];

        nodes[device["mac"]] = node;

        return node;
    }
    
    function initChildren(parentNode, devices, stats)
    {
        let connectedDevices = Object.values(devices).filter(data => data["connection"] && parentNode["device"]["mac"] == data["connection"]["target_mac"]);
        
        for( i in connectedDevices)
        {
            if( connectedDevices[i]["mac"] in nodes )
            {
                continue;
            }
          
            childNode = initNode(connectedDevices[i], stats);
            parentNode["children"].push(childNode);

            if( childNode["device"]["connected_from"].length > 0 )
            {
                initChildren(childNode, devices, stats);
            }
        }
    }
    
    function buildStructure()
    {
        nodes = {};

        Object.values(devices).forEach(function(device)
        {
            device["connected_from"] = [];
        });

        Object.values(devices).forEach(function(device)
        {
            if( !device["connection"] || !devices[device["connection"]["target_mac"]] ) return;
            
            devices[device["connection"]["target_mac"]]["connected_from"].push(device);
        });

        let rootDevices = Object.values(devices).filter(data => root_device_mac == data["mac"] );
        if( rootDevices.length > 0 )
        {
            rootNode = initNode(rootDevices[0], stats);
        
            if( rootNode["device"]["connected_from"].length > 0 )
            {
                initChildren(rootNode, devices, stats);
            }
        }
        else
        {
            rootNode = null;
        }
    }

    function processData(data)
    {
        //console.log(rootNode);

        if( data.hasOwnProperty("root") ) root_device_mac = data["root"];
        
        // **** PROCESS DEVICES ****
        let replacesNodes = data["devices"]["replace"];
        
        let now = new Date().getTime();
        let _devices = {}
        if( replacesNodes ) devices = {}
        data["devices"]["values"].forEach(function(device)
        {
            if( mx.Page.isDemoMode() )
            {
                if( demo_mac_map[device["mac"]] == undefined ) demo_mac_map[device["mac"]] = "XX:XX:XX:XX:XX:XX".replace(/X/g, function() { return "0123456789ABCDEF".charAt(Math.floor(Math.random() * 16)) });
                device["_demo_mac"] = demo_mac_map[device["mac"]];

                if( demo_ip_map[device["ip"]] == undefined ) demo_ip_map[device["ip"]] = "192.168.77." + Object.keys(demo_ip_map).length;
                device["_demo_ip"] = demo_ip_map[device["ip"]];
            }

            device["update"] = now;
            devices[device["mac"]] = device;
            _devices[device["mac"]] = device;
        });
        
        // **** SORT DEVICES ****
        if( data["devices"]["values"].length > 0 )
        {
            _devices = Object.values(devices).sort(function(a, b)
            {
                if( a.ip == null ) return -1;
                if( b.ip == null ) return 1;
                
                if( a.ip.length > b.ip.length ) return 1;
                if( a.ip.length < b.ip.length ) return -1;
                
                return a.ip > b.ip;
            });
            
            devices = {}
            _devices.forEach(function(device)
            {
                devices[device["mac"]] = device;
            });
        }
        
        // **** BUILD REPLACED STRUCTURE ****
        if( replacesNodes || rootNode == null ) 
        {
            if( rootNode == null ) mx.Error.confirmSuccess();
            
            buildStructure();
            
            _devices = devices;
            replacesNodes = true;
        }
        // **** UPDATE STRUCTURE ****
        else
        {
            Object.values(nodes).forEach(function(node)
            {
                node["device"] = devices[node["device"]["mac"]];
            });
        }
        
        // **** PROCESS GROUPS ****
        data["groups"]["added"].forEach(function(group)
        {
            group["update"] = now;
            groups[group["gid"]] = group;
        });
        data["groups"]["modified"].forEach(function(group)
        {
            group["update"] = now;
            groups[group["gid"]] = group;
        });
        data["groups"]["deleted"].forEach(function(group)
        {
            delete groups[group["gid"]];
        });

        // **** PROCESS STATS ****
        data["stats"]["added"].forEach(function(stat)
        {
            stat["update"] = now;
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            stats[key] = stat;
        });
        data["stats"]["modified"].forEach(function(stat)
        {
            stat["update"] = now;
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            stats[key] = stat;
        });
        data["stats"]["deleted"].forEach(function(stat)
        {
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            delete stats[key];
        });
        
        Object.values(devices).forEach(function(device)
        {
            device["isOnline"] = isOnline(device);
            device["deviceStat"] = getDeviceStat(device);
            device["interfaceStat"] = getInterfaceStat(device);
            
            if( device["deviceStat"] && device["deviceStat"]["update"] > device["update"] ) device["update"] = device["deviceStat"]["update"];
            if( device["interfaceStat"] && device["interfaceStat"]["update"] > device["update"] ) device["update"] = device["interfaceStat"]["update"];
            
            _groups = [];
            if( device["connection"] )
            {
                device["connection"]["details"].forEach(function(details)
                {
                    if( details["gid"] ) _groups.push(getGroup(details["gid"]));
                });
            }
            device["groups"] = _groups;
            
            device["wifi_signal"] = "";
            device["wifi_band"] = "";
            device["wifi_ssid"] = "";
            if( _groups.length > 0 && device["interfaceStat"] )
            {
                let signal = getDeviceSignal(device);
                if( signal )
                {
                    device["wifi_signal"] = signal["stat"].details.signal["value"];
                    device["wifi_band"] = signal["group"].details.band["value"];
                    device["wifi_ssid"] = signal["group"].details.ssid["value"];
                }
            }
        });
        
        //console.log(stats);
        
        if( rootNode == null )
        {
            mx.Error.handleError( mx.I18N.get("Network analysis is in progress")  );
        }
        else
        {
            if( isTable)
            {
                //mx.NetworkTable.draw( nodes, groups, stats);
            }
            else
            {
                mx.NetworkStructure.draw( activeTerm, replacesNodes ? rootNode : null, groups, stats);
            }
        }
    }
        
    ret.init = function()
    { 
        mx.I18N.process(document);
        
        mx.NetworkTooltip.init();
        
        //refreshDaemonState(null, function(state){});
        
        let socket = mx.ServiceSocket.init('system_service');
        socket.on("connect", (socket) => socket.emit('call', "network_data"));
        socket.on("network_data", (data) => processData(data));
        
        mx.$("#networkToolbar .networkDisplay.button").addEventListener("click",function()
        {
            isTable = !isTable;

            if( isTable )
            {
                mx.$("#networkToolbar .networkDisplay.button span").className = "icon-flow-tree";
                mx.NetworkTable.draw( activeTerm, nodes, groups, stats);
            }
            else
            {
                mx.$("#networkToolbar .networkDisplay.button span").className = "icon-table";
                mx.NetworkStructure.draw( activeTerm, rootNode, groups, stats);
            }
        });
        
        let searchInputBox = mx.$("#networkToolbar .networkSearchInput");
        let searchInputField = mx.$("#networkToolbar .networkSearchInput input");
        let lastBlur = 0;
        
        mx.$("#networkToolbar .networkSearch.button").addEventListener("click",function()
        {
            if( window.performance.now() - lastBlur  < 500 )
                return;
            
            searchInputBox.classList.toggle("active");
            
            if( searchInputBox.classList.contains("active") ) 
            {
                searchInputField.focus();
            }
        });
        
        searchInputField.addEventListener("keyup",function(event)
        {
            if(event.keyCode == 27 ) // esc
            {
                searchInputBox.classList.toggle("active");
                searchInputField.blur();
            }
            else
            {
                var _term = searchInputField.value.toLowerCase();
                if( _term == activeTerm )
                    return;

                activeTerm = _term.toLowerCase();
                
                if( isTable)
                {
                    mx.NetworkTable.search(activeTerm);
                }
                else
                {
                    mx.NetworkStructure.search(activeTerm);
                }
            }
        });
        
        searchInputField.addEventListener("focus",function(event)
        {
            searchInputField.select();
        });

        searchInputField.addEventListener("blur",function(event)
        {   
            if( searchInputField.value == "" )
            {
                searchInputBox.classList.remove("active");
                lastBlur = window.performance.now();
            }
        });
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );
</script>
</head>
<body class="inline">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Network visualizer")); } );</script>
<div class="contentLayer error"></div>
<div id="networkDataPages">
<div id="networkStructure"></div>
<div id="networkList"></div>
</div>
<div id="networkToolbar"><div class="networkDisplay form button"><span class="icon-table"></span></div><div class="networkSearch form button"><span class="icon-search-1"></span></div><div class="networkSearchInput"><input></div></div>
</body>
</html>
