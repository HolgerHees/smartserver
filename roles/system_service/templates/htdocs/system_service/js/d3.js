mx.D3 = (function( ret ) 
{
    //let boxMargin = 3;
    let boxPadding = 3;
    let boxWidth = 150;
    let boxHeight = 0;

    let bodyRect = {};
    let bodyWidth = null;
    let bodyHeight = null;

    let link = null;
    let node = null;
    
    let d3root = null;
    
    let groups = null;
    let devices = null;
    let stats = null;
    
    let root = null;
    
    function initNode(device, stats, processedNodes)
    {
        processedNodes[device["mac"]] = true;

        let node = {};
        node["name"] = device["mac"];
        node["device"] = device;
        node["children"] = [];

        node["device_stat"] = stats[device["mac"]] ? stats[device["mac"]] : null;
        if( device["connection"] )
        {
            key = device["connection"]["target_mac"]+":"+device["connection"]["target_interface"]
            node["interface_stat"] = stats[key] ? stats[key] : null;
        }

        return node;
    }
    
    function initChildren(rootNode, devices, stats, processedNodes)
    {
        let connectedDevices = devices.filter(data => data["connection"] && rootNode["device"]["mac"] == data["connection"]["target_mac"]);
        
        for( i in connectedDevices)
        {
            if( connectedDevices[i]["mac"] in processedNodes )
            {
                continue;
            }
          
            childNode = initNode(connectedDevices[i], stats, processedNodes);
            rootNode["children"].push(childNode);

            if( childNode["device"]["connected_from"].length > 0 )
            {
                initChildren(childNode, devices, stats, processedNodes);
            }
        }
    }
    
    ret.drawCircles = function(root_device_mac, _devices, _groups, _stats, refresh_interval)
    {
        if( _groups )
            groups = _groups;
        
        if( _devices )
            devices = _devices;
        
        if( _stats )
            stats = _stats;
        
        if( _devices )
        {
            let processedNodes = {};
            let rootNode = null;
            
            device_uid_map = {}
            devices.forEach(function(device)
            {
                device["connected_from"] = [];
                device_uid_map[device["mac"]] = device;
            });

            devices.forEach(function(device)
            {
                if( !device["connection"] || !device_uid_map[device["connection"]["target_mac"]] ) return;
                
                device_uid_map[device["connection"]["target_mac"]]["connected_from"].push(device["mac"]);
            });

            let endCount = devices.filter(data => data["connected_from"].length == 0 ).length;
            
            let rootDevices = devices.filter(data => root_device_mac == data["mac"] );
            rootNode = initNode(rootDevices[0], stats, processedNodes);
        
            if( rootNode["device"]["connected_from"].length > 0 )
            {
                initChildren(rootNode, devices, stats, processedNodes);
            }
            
            root = d3.hierarchy(rootNode);

            initTree(endCount);
        }
        else if( _stats )
        {            
            root.descendants().forEach(function(_data)
            {
                let mac = _data["data"]["device"]["mac"];
                
                if(mac in stats) 
                {
                    _data["data"]["device_stat"] = stats[mac];
                }
                if( _data["data"]["device"]["connection"] )
                {
                    key = _data["data"]["device"]["connection"]["target_mac"]+":"+_data["data"]["device"]["connection"]["target_interface"]
                    if(key in stats)
                    {
                        _data["data"]["interface_stat"] = stats[key];
                    }
                }
            });

            redrawState();
        }
    }
    
    ret.init = function(devices, groups, traffic)
    {
    }
    
    function initTree(endCount)
    {
        bodyRect = document.body.getBoundingClientRect();
        bodyWidth = bodyRect.width;
        bodyHeight = bodyRect.height;
        
        const width = 1000;//bodyWidth;
        const height = 1000;//bodyWidth;
        //scaleFactor = ( bodyWidth > bodyHeight ? bodyWidth : bodyHeight ) / 1000;
        //const width = bodyWidth / scaleFactor;
        //const height = bodyHeight / scaleFactor;

        // Compute the layout.
        let dx = ( height / endCount ) - ( 2 * boxPadding ) ;
        if( dx > 30 ) dx = 30;
        let dy = width / (root.height + 1);

        d3.tree().nodeSize([dx + 2, dy])(root);
        //d3.tree().size([300, 200])(root);
        
        boxHeight = dx;
        
        //console.log(boxHeight);

        // Center the tree.
        let x0 = Infinity;
        let x1 = -x0;
        root.each(d => {
            if (d.x > x1) x1 = d.x;
            if (d.x < x0) x0 = d.x;
        });
            
        // Compute the default height.
        if (height === undefined) height = x1 - x0 + dx * 2;
        
        if( root.children && root.children.length == 1 )
        {
            root.x = dx * 3;
            root.y = dy;
        }
        
        const svg = d3.selectAll("#network")
            //.attr("viewBox", [-dy / 2 + ( dy / 3 ), x0 - dx, width, width])
            .attr("viewBox", [0, 0, width, height])
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("font-family", "sans-serif");
        
        svg.selectAll("g").remove()
        
        link = svg.append("g")
                .classed("links", true)
            .selectAll("path")
                .data(root.links())
            .join("path")
                .attr("d", linkGenerator);
                
        //var tooltip = d3.select("#tooltip");
                        
        node = svg.append("g")
            .classed("nodes", true)
            .selectAll("a")
            .data(root.descendants())
            .join("a")
        //      .attr("xlink:href", link == null ? null : d => link(d.data, d))
        //      .attr("target", link == null ? null : linkTarget)
            .attr("transform", d => `translate(${d.y},${d.x})`)
            .attr("id", function(d) { return d.data.uid; })
            .on("mouseenter", function(e, d){ 
                e.stopPropagation();
                showTooltip(d, link);
            })
            .on("mousemove", function(e, d){
                e.stopPropagation();
                positionTooltip(d, this);
            })
            .on("mouseleave", function(){
                link
                    .classed("online", false)
                    .classed("offline", false);
            })
            .on("click", function(e, d){
                e.stopPropagation();

                if( mx.Core.isTouchDevice() )
                {
                    showTooltip(d, link);
                }
                else
                {
                    toogleTooltip(d);
                }
            });
                
                
            svg.on("click", function(e, d){
                mx.Tooltip.hide();
            });

        node.append("rect")
            .attr("class", d => "container " + ( d.data["device"] ? d.data["device"]["type"] : "" ) )
            .attr("width", boxWidth)
            .attr("height", boxHeight);

        node.append("circle")
            .attr("class", d => ( isOnline(d) ? "online" : "offline" ) )
            .attr("cx", 143)
            .attr("cy", 7)
            .attr("r", 3);

        //  if (title != null) node.append("title")
        //      .text(d => title(d.data, d));

        let font_size = boxHeight / 2.5
            
        node.append("text")
            .classed("identifier", true)
            .attr("dy", font_size * 1.1)
            .attr("x", "5")
            .attr("font-size", font_size)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data["device"]["ip"] ? d.data["device"]["ip"] : d.data["device"]["mac"] ).each( wrap );
        
        node.append("text")
            .classed("name", true)
            .attr("dy", font_size * 2 * 1.1)
            .attr("x", "5")
            .attr("font-size", font_size * 0.9)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", "start")
            .text(d => d.data["device"]["dns"] ? d.data["device"]["dns"] : d.data["device"]["type"] ).each( wrap );

        let details_font_size = boxHeight / 4;
        let details_text = node.append("text")
            .classed("details", true)
            .attr("font-size", details_font_size);
        details_text.append("tspan").classed("top", true);
        details_text.append("tspan").classed("bottom", true);
        details_text.each( setDetailsContent );

        let traffic_background = node.append("rect").classed("traffic", true);

        let traffic_font_size = boxHeight / 4;
        let traffic_text = node.append("text")
            .classed("traffic", true)
            .attr("font-size", traffic_font_size);
        traffic_text.append("tspan").classed("in", true);
        traffic_text.append("tspan").classed("out", true);

        let root_traffic_text = node.selectAll("text.traffic").filter(d => d == root );
        root_traffic_text.append("tspan").classed("wan_in", true)
        root_traffic_text.append("tspan").classed("wan_out", true);

        traffic_text.each( setTrafficContent );

        traffic_background.each( setTrafficBackground );
        
        let _svg = document.querySelector('svg');
        const { xMin, xMax, yMin, yMax } = [..._svg.children].reduce((acc, el) => {
            const { x, y, width, height } = el.getBBox();
            if (!acc.xMin || x < acc.xMin) acc.xMin = x;
            if (!acc.xMax || x + width > acc.xMax) acc.xMax = x + width;
            if (!acc.yMin || y < acc.yMin) acc.yMin = y;
            if (!acc.yMax || y + height > acc.yMax) acc.yMax = y + height;
            return acc;
        }, {});
        //console.log(xMin, yMin, xMax - xMin, yMax - yMin);
        svg.attr("viewBox", [xMin - 10, yMin - 10, (xMax - xMin) + 20, (yMax - yMin) + 20])
    }
    
    function redrawState() {
        node.selectAll("text.details").each( setDetailsContent );

        node.selectAll("text.traffic").each( setTrafficContent );
        node.selectAll("rect.traffic").each( setTrafficBackground );

        let online_circle = node.selectAll("circle");
        online_circle.attr("class", d => ( isOnline(d) ? "online" : "offline" ) );
    };
    
    function setDetailsContent(d)
    {
        let text = d3.select(this);
        let font_size = text.attr("font-size");

        let top_span = text.select(".top");
        let bottom_span = text.select(".bottom");
        
        top_span.text(d =>"");
        bottom_span.classed("hs", false);
        bottom_span.text(d =>"");

        if( d.data.device.gids.length > 0 )
        {
            d.data.device.gids.forEach(function(gid){
                let group = groups.filter(group => group["gid"] == gid );
                if( group.length == 1 && group[0].type == "wifi"  )
                {
                    let stat = d.data.interface_stat
                    
                    bottom_span.text(d => group[0].details.band["value"] + " • " + stat.details.signal["value"] + "db");
                    if( group[0].details.band["value"] == "5g" )
                        bottom_span.classed("hs", true);
                    
                    top_span.text(d => group[0].details.ssid["value"]);
                    
                    let textLength = top_span.node().getComputedTextLength() + 3;
                    top_span.attr("x", boxWidth - textLength );
                    top_span.attr("y", boxHeight - 3 - font_size );

                    textLength = bottom_span.node().getComputedTextLength() + 3;
                    bottom_span.attr("x", boxWidth - textLength );
                    bottom_span.attr("y", boxHeight - 3 );
                }
            });
        }  
        else if(root == d && d.data.interface_stat.details["wan_state"])
        {
            bottom_span.text(d => "WAN: " + d.data.interface_stat.details["wan_state"]["value"]);
            let textLength = bottom_span.node().getComputedTextLength() + 3;
            bottom_span.attr("x", boxWidth - textLength );
            bottom_span.attr("y", boxHeight - 3 );
        }
    }
    
    function setTrafficContent(d)
    {
        let text = d3.select(this);
        let font_size = text.attr("font-size");
        
        let position = "default";
        if( root.children && root.children.length == 1 )
        {
            if( root==d.parent || root==d )
            {
                position = "bottom";
            }
            /*else if(  )
            {
                position = "top";
                
                if( d.data.interface_stat && d.data.interface_stat.traffic )
                {
                    let wan_in_data = formatTraffic( d.data.interface_stat.traffic["in_avg"]);
                    let wan_in_span = text.select(".wan_in");
                    wan_in_span.text(d => wan_in_data == 0 ? "" : "⇨ " + wan_in_data );
                    
                    let textLength = wan_in_span.node().getComputedTextLength() + 3;
                    wan_in_span.attr("x", boxWidth / 2 - 2 - textLength );
                    wan_in_span.attr("y", boxHeight + font_size * 1.5 );
                    
                    let wan_out_data = formatTraffic( d.data.interface_stat.traffic["out_avg"]);
                    let wan_out_span = text.select(".wan_out");
                    wan_out_span.text(d => wan_out_data == 0 ? "" : "⇨ " + wan_out_data );
                    textLength = wan_out_span.node().getComputedTextLength() + 3;
                    wan_out_span.attr("x", boxWidth / 2 + 4 );
                    wan_out_span.attr("y", boxHeight + font_size * 1.5);
                }
            }*/
        }
            
        if( position != "default" )
            text.node().parentNode.querySelector("rect.traffic").style.setProperty("fill", "transparent");

        let traffic_stat = d.data.interface_stat && d.data.interface_stat.traffic ? d.data.interface_stat.traffic : null;
        if( !traffic_stat ) return;
       
        let row = 0;
        
        let in_data = formatTraffic( traffic_stat["in_avg"]);
        let out_data = formatTraffic( traffic_stat["out_avg"]);
        
        let offset = in_data != 0 && out_data != 0  ? font_size * 0.1 : font_size * 0.9;
        
        let in_span = text.select(".in");
        if( in_data != 0 ) 
        {
            row += 1;
            in_span.text(d => "⇨ " + in_data );
            let textLength = in_span.node().getComputedTextLength() + 3;
            if( position != "default" )
            {
                in_span.attr("x", boxWidth / 2 - 2 - textLength );
                if( position == "bottom" ) 
                {
                    in_span.attr("y", boxHeight + font_size * 1.5 );
                }
                else
                {
                    in_span.attr("y", font_size * -0.8 );
                }
            }
            else
            {
                in_span.attr("x", textLength * -1);
                in_span.attr("y", font_size * 1.5 * row + offset);
            }
        }
        else
        {
            in_span.text(d => "");
        }

        let out_span = text.select(".out");
        if( out_data != 0 )
        {
            row += 1;
            out_span.text(d => "⇦ " + out_data );
            let textLength = out_span.node().getComputedTextLength() + 3;
            if( position != "default" )
            {
                out_span.attr("x", boxWidth / 2 + 4 );
                if( position == "bottom" ) 
                {
                    out_span.attr("y", boxHeight + font_size * 1.5);
                }
                else
                {
                    in_span.attr("y", font_size * -0.8 );
                }
            }
            else
            {
                out_span.attr("x", textLength * -1);
                out_span.attr("y", font_size * 1.5 * row + offset);
            }
        }
        else
        {
            out_span.text(d => "");
        }
    }
    
    function formatTraffic(traffic)
    {
        if( traffic > 100000000 ) return Math.round( traffic / 1000000 ).toFixed(1) + " MB/s";                  // >= 100MB
        
        if( traffic > 1000000 ) return ( Math.round( ( traffic / 1000000 ) * 10 ) / 10 ).toFixed(1) + " MB/s";  // >= 1MB

        if( traffic > 100000 ) return Math.round( traffic / 1000 ).toFixed(1) + " KB/s";                        // >= 100KB
        
        if( traffic > 1000 ) return ( Math.round( ( traffic / 1000 ) * 10 ) / 10 ).toFixed(1) + " KB/s";        // >= 1KB
        
        if( traffic > 100 ) return ( Math.round(traffic / 100) / 10 ).toFixed(1) + " KB/s";
        
        return 0;
    }

    function setTrafficBackground(d)
    {
        let self = d3.select(this);
        
        let rect = self.node().parentNode.querySelector("text.traffic").getBBox();
        self.attr("x", rect.x - 1);
        self.attr("y", rect.y - 1);
        self.attr("width", rect.width + 1);
        self.attr("height", rect.height + 1);
    }
    
    function linkGenerator(d) {
        if( root == d.source && root.children.length == 1)
        {
            let path = d3.linkHorizontal()
                .source(function (d) {
                    return [ d.source.y + (boxWidth / 2), (d.source.x + d.source.height / 2) + boxHeight / 2 + boxHeight * 1.5 ];
                })
                .target(function (d) {
                    return [ d.target.y + (boxWidth / 2), (d.target.x + d.target.height / 2) + boxHeight / 2 ];
                });
                    
            return path(d);
        }
        else
        {
            let path = d3.linkHorizontal()
                .source(function (d) {
                    return [ d.source.y + boxWidth - 30, (d.source.x + d.source.height / 2) + boxHeight / 2 ];
                })
                .target(function (d) {
                    return [ d.target.y, (d.target.x + d.target.height / 2) + boxHeight / 2 ];
                });
                    
            return path(d);
        }
    }
    
    function showTooltip(d,link)
    {
        let device = d.data.device
        let html = "<div>";
        if( device.ip ) html += "<div><div>IP:</div><div>" + device.ip + "</div></div>";
        if( device.dns ) html += "<div><div>DNS:</div><div>" + device.dns + "</div></div>";
        if( device.mac ) html += "<div><div>MAC:</div><div>" + device.mac + "</div></div>";
        
        if( d.data.device_stat )
        {
            let dateTimeMsg = "";
            
            if( isOnline(d) )
            {
                dateTimeMsg = "Online";
            }
            else
            {
                let lastSeenTimestamp = Date.parse(d.data.device_stat["offline_since"]);
                let lastSeenDatetime = new Date(lastSeenTimestamp)
                
                dateTimeMsg = lastSeenDatetime.toLocaleTimeString();
                if( ( ( new Date().getTime() - lastSeenTimestamp ) / 1000 ) > 60 * 60 * 12 )
                {
                    dateTimeMsg = lastSeenDatetime.toLocaleDateString() + " " + dateTimeMsg
                }
                
                dateTimeMsg = "Offline since " + dateTimeMsg;
            }
            
            html += "<div><div>Status:</div><div>" + dateTimeMsg + "</div></div>";
        }
        if( device.info ) html += "<div><div>Info:</div><div>" + device.info + "</div></div>";
        html += "<div><div>Type:</div><div>" + device.type + "</div></div>";
    
        html += showRows(device.details,"Details","rows");
        html += showRows(device.services,"Services","rows");
        //html += showRows(device.ports,"Ports","rows");
        
        connection_data = {}
        device.gids.forEach(function(gid){
            let group = groups.filter(group => group["gid"] == gid );
            if( group[0]["type"] == "wifi" )
                connection_data = group[0]["details"]
            else
                html += showRows(group[0]["details"],group[0]["type"],"rows");
        });
        
        if( device.connection )
        {
            if( device.connection["vlans"] )
                connection_data["Vlan"] = "" + device.connection["vlans"];
            if( device.connection["target_interface"] && device.connection["type"] != "wifi" )
                connection_data["Port"] = device.connection["target_interface"];
            
            if( d.data.interface_stat )
            {
                if( d.data.interface_stat["speed"] )
                {
                    let inSpeed = d.data.interface_stat["speed"]["in"];
                    let outSpeed = d.data.interface_stat["speed"]["out"];
                    
                    if( inSpeed != null )
                    {
                        let duplex = "";
                        if( "duplex" in d.data.interface_stat["details"] )
                        {
                            duplex += " - " + ( d.data.interface_stat["details"]["duplex"]["value"] == "full" ? "FullDuplex" : "HalfDuplex" );
                        }
                        
                        connection_data["Speed"] = formatSpeed(inSpeed) + (inSpeed == outSpeed ? '' : ' RX / ' + formatSpeed(outSpeed) + " TX" ) + duplex;
                    }
                }

                Object.entries(d.data.interface_stat["details"]).forEach(function([key, value])
                {
                    if( key == "duplex" )
                        return;
                        
                    let _value = value["value"];
                    if( value["format"] == "attenuation" ) 
                        _value += " db";
                    
                    connection_data[key] = _value;
                });
            }
        }
        
        html += showRows(connection_data,"Network","rows");
            
        if( d.data.device_stat )
        {
            Object.entries(d.data.device_stat["details"]).forEach(function([key, value])
            {
                let _value = value["value"];
                html += "<div><div>" + capitalizeFirstLetter(key) + ":</div><div>" + _value + "</div></div>";
            });
        }

        html += "</div>"
        
        mx.Tooltip.setText(html);
        
        link
            .classed("online", false)
            .classed("offline", false)
            .filter(l => l.source.data === d.data || l.target.data === d.data)
            .classed("online", isOnline(d))
            .classed("offline", !isOnline(d));
    }
        
    function toogleTooltip(d)
    {
        let device = d.data.device
        mx.Tooltip.toggle();
    }
    
    function positionTooltip(d, element)
    {
        let device = d.data.device
        element = element.querySelector("rect.container");
        
        let nodeRect = element.getBoundingClientRect();
        let tooltipRect = mx.Tooltip.getRootElementRect();

        let arrowOffset = 0;
        let arrowPosition = "right";
        
        let top = nodeRect.top;
        if( top + tooltipRect.height > bodyHeight ) 
        {
            top = bodyHeight - tooltipRect.height - 6;
            arrowOffset = tooltipRect.height - ( bodyHeight - ( nodeRect.top + nodeRect.height / 2 ) );
        }
        else
        {
            arrowOffset = nodeRect.height / 2;
        }

        let left = nodeRect.left - tooltipRect.width - 6;
        if( left < 0 )
        {
            left = nodeRect.left + nodeRect.width + 6;
            arrowPosition = "left";
        }

        mx.Tooltip.show(left, top, arrowOffset, arrowPosition );
        window.setTimeout(function(){ mx.Tooltip.getRootElement().style.opacity="1"; },0);
    }
    
    function wrap( d ) {
        var self = d3.select(this),
            textLength = self.node().getComputedTextLength(),
            text = self.text();
        while ( ( textLength > 145 )&& text.length > 0) {
            text = text.slice(0, -1);
            self.text(text + '...');
            textLength = self.node().getComputedTextLength();
        }
    }
        
    function capitalizeFirstLetter(string) {
        string = string.replace("_", " ");
        
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    function formatSpeed(speed)
    {
            if( speed >= 1000000000 ) return Math.round( speed * 10 / 1000000000 ) / 10 + " GBit";
            else if( speed >= 1000000 ) return Math.round( speed * 10 / 1000000 ) / 10 + " MBit";
            else if( speed >= 1000 ) return Math.round( speed * 10 / 1000 ) / 10 + " KBit";
            else return speed + " Bit";
    }
    
    function formatDetails(key, value)
    {
        if( ["ssid"].indexOf(key) != -1 )
        {
                key = key.toUpperCase()
        }
        else
        {
                key = capitalizeFirstLetter(key);
        }
        
        return [key, value]
    }
    
    function isOnline(d)
    {
        if( d.data.device.type == 'hub' )
        {
            let all_children_online = true;
            for(let child of d.data.children) 
            {
                if( !child.device_stat || child.device_stat.offline_since != null )
                {
                    all_children_online = false;
                    break;
                }
            }
            return all_children_online;
        }

        return d.data.device_stat && d.data.device_stat.offline_since == null;
    }

    function showRows(rows, name, cls)
    {
        let html = '';
        if( Object.entries(rows).length > 0)
        {
            html += "<div><div>" + capitalizeFirstLetter(name) + ":</div><div class='" + cls + "'><div>";
            Object.entries(rows).forEach(function([key, value])
            {
                [key, value] = formatDetails(key, value)
                
                if( value && typeof( value ) == "object" )
                {
                    value = value["value"]
                }
                html += "<div><div>" + key + "</div><div>" + value + "</div></div>";
            });
            html += "</div></div></div>";
        }
        return html;
    }


    return ret;
})( mx.D3 || {} );
