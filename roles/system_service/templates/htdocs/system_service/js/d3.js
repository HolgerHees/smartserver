mx.D3 = (function( ret ) 
{
    //let boxMargin = 3;
    let box_padding = 3;
    let box_width = 150;
    let box_height = 0;
    let font_size = 0;

    let groups = null;
    let stats = null;
    
    let root = null;
    
    let link = null;
    let node = null;
    
    let active_tooltip_d = null;
    
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

    ret.drawStructure = function( rootNode, _groups, _stats) {
        groups = _groups;
        stats = _stats;
        
        if( rootNode )
        {
            root = d3.hierarchy(rootNode);

            depthCount = {}
            root.descendants().forEach(function(data){
                if( !depthCount.hasOwnProperty(data["depth"]) ) depthCount[data["depth"]] = 0;
                depthCount[data["depth"]] += 1;
            });

            let endCount = 0;
            Object.values(depthCount).forEach(function(value)
            {
                if( value > endCount ) endCount = value;
            });

            initTree(endCount);
            refreshTooltip();
        }
        else if( node )
        {
            redrawState();
            refreshTooltip();
        }
    }
    
    ret.openChart = function(ip, has_traffic, has_wifi)
    {
        let timeranges = {
            "now-3h": mx.I18N.get("Last 3 hours"),
            "now-6h": mx.I18N.get("Last 6 hours"),
            "now-12h": mx.I18N.get("Last 12 hours"),
            "now-24h": mx.I18N.get("Last 24 hours"),
            "now-2d": mx.I18N.get("Last 2 days"),
            "now-7d": mx.I18N.get("Last 7 days")
        };

        let height = ( window.innerHeight * 0.8 ) / 2;
        let url_prefix = 'https://grafana.' + document.location.host;
        let url = url_prefix + '/d-solo/system-info/system-info?theme=' + ( mx.Page.isDarkTheme() ? 'dark': 'light' ) + '&var-host=' + ip + '&orgId=1';
        let body = "";
        if( has_traffic ) body += '<iframe src="' + url + '&panelId=7&from=now-6h&to=now" width="100%" height="' + height + '" frameborder="0"></iframe>';
        if( has_wifi ) body += '<iframe src="' + url + '&panelId=4&from=now-6h&to=now" width="100%" height="' + height + '" frameborder="0"></iframe>';

        let dialog = null;
        let selectButton = null;
        
        function changeTimerange(btn, timerange)
        {
            selectButton.setText(btn.innerHTML);
            
            let iframes = dialog.getRootElement().querySelectorAll("iframe");
            iframes.forEach(function(iframe)
            {
                iframe.src = iframe.src.replace(/&from=[^&]+&/i,"&from=" + timerange + "&");
            });
        }
       
        dialog = mx.Dialog.init({
            body: body,
            buttons: [
                { "text": timeranges["now-6h"], "class": "timeRange", "callback": function(event){ selectButton.toggle(event); } },
                { "text": mx.I18N.get("Open Grafana"), "callback": function(){ window.open(url_prefix + '/d/system-info/system-info?orgId=1&theme=' + ( mx.Page.isDarkTheme() ? 'dark': 'light' ), '_blank'); }  },
                { "text": mx.I18N.get("Close") },
            ],
            class: "confirmDialog",
            destroy: true
        });
        
        let values = []
        Object.entries(timeranges).forEach(function([key,text])
        {
            values.push({ "text": text, "onclick": function(selection){ changeTimerange(selection, key); } });
        })
        
        selectButton = mx.Selectbutton.init({
            values: values,
            class: "alignLeft",
            elements: {
                button: dialog.getRootElement().querySelector(".timeRange")
            }
        });

        dialog.open();
        mx.Page.refreshUI(dialog.getRootElement());
    }
    
    function initTree(endCount)
    {
        const width = 1000;
        const height = 1000;
        
        // Compute the layout.
        let dx = ( height / endCount ) - ( 2 * box_padding ) ;
        if( dx > 30 ) dx = 30;
        let dy = width / (root.height + 1);

        d3.tree().nodeSize([dx + 2, dy])(root);
        //d3.tree().size([300, 200])(root);
        
        box_height = dx;
        font_size = box_height / 3;
        //if( font_size > 10 ) font_size = 10;
        //console.log(font_size);
        //console.log(box_height);

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
                showTooltip(d);
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
                    showTooltip(d);
                }
                else
                {
                    toggleTooltip(d);
                }
            });
                
                
            svg.on("click", function(e, d){
                hideTooltip();
            });

        node.append("rect")
            .attr("class", d => "container " + d.data.device.type )
            .attr("width", box_width)
            .attr("height", box_height);

        node.append("circle")
            .attr("class", d => ( isOnline(d.data.device) ? "online" : "offline" ) )
            .attr("cx", 143)
            .attr("cy", 7)
            .attr("r", 3);

        //  if (title != null) node.append("title")
        //      .text(d => title(d.data, d));

        node.append("text")
            .classed("identifier", true)
            .attr("dy", font_size * 1.2)
            .attr("x", "2.5")
            .attr("font-size", font_size)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data["device"]["ip"] ? d.data["device"]["ip"] : d.data["device"]["mac"] ).each( wrap );
            
        let details_font_size = box_height / 4;

        node.append("text")
            .classed("name", true)
            .attr("dy", font_size * 2.2 * 1.2)
            .attr("x", "2.5")
            .attr("font-size", font_size * 0.9)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", "start")
            .text(d => d.data["device"]["dns"] ? d.data["device"]["dns"] : d.data["device"]["type"] ).each( wrap );

        let details_info = node.append("foreignObject")
            .classed("details", true)
            .attr("font-size", details_font_size)
            .attr("height", box_height - 10 )
            .attr("width", box_width / 2 - 3)
            .attr("y", 10 )
            .attr("x", box_width / 2);
        details_info.each( setDetailsContent );

        let traffic_background = node.append("rect").classed("traffic", true);

        let traffic_font_size = box_height / 4;
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
        node.selectAll("foreignObject.details").each( setDetailsContent );

        node.selectAll("text.traffic").each( setTrafficContent );
        node.selectAll("rect.traffic").each( setTrafficBackground );

        let online_circle = node.selectAll("circle");
        online_circle.attr("class", d => ( isOnline(d.data.device) ? "online" : "offline" ) );
    };
    
    function setDetailsContent(d)
    {
        let foreignobject = d3.select(this);
        
        foreignobject.html(d => "" );
        
        if( d.data.device.gids.length > 0 )
        {
            d.data.device.gids.forEach(function(gid){
                let group = getGroup(gid);
                if( group && group.type == "wifi"  )
                {
                    let interface_stat = getInterfaceStat(d.data.device);
                    
                    // *** Should never happen. Otherwise it is a bug in system_service
                    /*if( interface_stat == null )
                    {
                        console.log(d.data.device)
                        console.log(stats)
                        return;
                    }*/

                    let signal_value = interface_stat.details.signal["value"];
                    let band_value = group.details.band["value"];
                    
                    let offset = 0;//band_value == "2g" ? 0 : 10;
                    
                    if( signal_value > -50 - offset ) signal_class = "highest";
                    else if( signal_value > -67 - offset ) signal_class = "high";
                    else if( signal_value > -75 - offset ) signal_class = "medium";
                    else if( signal_value > -85 - offset ) signal_class = "low";
                    else signal_class = "lowest";
                    
                    let html = "<div class='top'>" + group.details.ssid["value"] + "</div>";
                    html += "<div class='bottom'><span class='band c" + band_value + "'>" + band_value + "</span> • <span class='signal " + signal_class + "'>" + signal_value + "db</span></div>";
                    foreignobject.html(d => html );
                    
                    //textLength = bottom_span.node().getComputedTextLength() + 3;
                    //bottom_span.attr("x", box_width - textLength );
                    //bottom_span.attr("y", box_height - 3 );
                }
            });
        }  
        else if(root == d )
        {
            let interface_stat = getInterfaceStat(d.data.device);
            if( interface_stat && interface_stat.details["wan_state"])
            {
                foreignobject.html(d => "<div class='top'>&nbsp;</div><div class='bottom'>WAN: " + interface_stat.details["wan_state"]["value"] + "</div>");
            }
        }
    }
    
    /*function setTrafficContentNeu(d)
    {
        let foreignobject = d3.select(this);
        let font_size = foreignobject.attr("font-size");
        
        let position = "default";
        if( root.children && root.children.length == 1 )
        {
            if( root==d.parent || root==d )
            {
                position = "bottom";
            }
        }
            
        if( position != "default" )
            foreignobject.node().parentNode.querySelector("rect.traffic").style.setProperty("fill", "transparent");

        let interface_stat = getInterfaceStat(d.data.device);
        if( !interface_stat || !interface_stat.traffic) return;
       
        let row = 0;
        
        let in_data = formatTraffic( interface_stat.traffic["in_avg"], false);
        let out_data = formatTraffic( interface_stat.traffic["out_avg"], false);
        
        let offset = in_data && out_data  ? font_size * 0.1 : font_size * 0.9;
        
        let html = '';
        if( in_data ) 
        {
            html += "<div class='in'>⇨ " + in_data + "</div>";
        }

        if( out_data )
        {
            html += "<div class='out'>⇦ " + out_data + "</div>";
        }
        
        foreignobject.html(d => "<div>" + html + "</div>" );
        
        let height = 0;
        let width = 0;
        
        //foreignobject.attr("height", 300).attr("width", 300);
        
        let childNodes = foreignobject.node().childNodes[0].childNodes;
        if( position == "bottom" )
        {
            childNodes.forEach(function(node)
            {
                let box = node.getBoundingClientRect();
                if( box.height > height ) height = box.height;
                width += box.width;
                
                console.log(box.width);
            });
            console.log(width);
            console.log("----");

            foreignobject.attr("x", box_width / 2 - width / 2).attr("y", box_height );
        }
        else
        {
            childNodes.forEach(function(node)
            {
                let box = node.getBoundingClientRect();
                height += box.height;
                if( box.width > width ) width = box.width;
            });
            foreignobject.attr("x", width * -1 - 5).attr("y", 0);
        }
        
        //foreignobject.attr("height", height).attr("width", width);

        //console.log(foreignobject.node().firstChild.getBoundingClientRect());
    }*/
    
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
        }
            
        if( position != "default" )
            text.node().parentNode.querySelector("rect.traffic").style.setProperty("fill", "transparent");

        let interface_stat = getInterfaceStat(d.data.device);
        if( !interface_stat || !interface_stat.traffic) return;
       
        let row = 0;
        
        let in_data = formatTraffic( interface_stat.traffic["in_avg"], false);
        let out_data = formatTraffic( interface_stat.traffic["out_avg"], false);
        
        let offset = in_data && out_data  ? font_size * 0.1 : font_size * 0.9;
        
        let in_span = text.select(".in");
        if( in_data ) 
        {
            row += 1;
            in_span.text(d => "⇨ " + in_data );
            let textLength = in_span.node().getComputedTextLength() + 3;
            if( position != "default" )
            {
                in_span.attr("x", box_width / 2 - 2 - textLength );
                if( position == "bottom" ) 
                {
                    in_span.attr("y", box_height + font_size * 1.5 );
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
        if( out_data )
        {
            row += 1;
            out_span.text(d => "⇦ " + out_data );
            let textLength = out_span.node().getComputedTextLength() + 3;
            if( position != "default" )
            {
                out_span.attr("x", box_width / 2 + 4 );
                if( position == "bottom" ) 
                {
                    out_span.attr("y", box_height + font_size * 1.5);
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
                    return [ d.source.y + (box_width / 2), (d.source.x + d.source.height / 2) + box_height / 2 + box_height * 1.5 ];
                })
                .target(function (d) {
                    return [ d.target.y + (box_width / 2), (d.target.x + d.target.height / 2) + box_height / 2 ];
                });
                    
            return path(d);
        }
        else
        {
            let path = d3.linkHorizontal()
                .source(function (d) {
                    return [ d.source.y + box_width - 30, (d.source.x + d.source.height / 2) + box_height / 2 ];
                })
                .target(function (d) {
                    return [ d.target.y, (d.target.x + d.target.height / 2) + box_height / 2 ];
                });
                    
            return path(d);
        }
    }
    
    function hideTooltip()
    {
        mx.Tooltip.hide();  
        active_tooltip_d = null;
    }
    
    function showTooltip(d)
    {
        active_tooltip_d = d;
        _buildTooltip(active_tooltip_d);
    }
    
    function refreshTooltip()
    {
        if( !active_tooltip_d ) return;
        
        active_device = root.descendants().filter(n => active_tooltip_d.data.device["mac"] == n.data.device["mac"] );
        if( active_device.length > 0 )
        {
            _buildTooltip(active_tooltip_d);
        }
        else
        {
            hideTooltip();
        }
    }
    
    function _buildTooltip(d)
    {
        let device = d.data.device
        let html = "<div>";
        if( device.ip ) 
        {
            let interface_stat = getInterfaceStat(device);
            let has_traffic = interface_stat && interface_stat.traffic.in_avg !== null;
            let has_wifi = device.connection["type"] == "wifi";
            
            html += "<div><div>IP:</div><div";
            if( has_traffic || has_wifi ) html += ' class="link" onclick="mx.D3.openChart(\'' + device.ip + '\', ' + ( has_traffic ? 'true' : 'false' ) + ', ' + ( has_wifi ? 'true' : 'false' ) + ')"';
            html += ">" + device.ip;
            if( has_traffic || has_wifi ) html += ' <span class="icon-chart-area"></span>';
            html += "</div></div>";
        }
        if( device.dns ) html += "<div><div>DNS:</div><div>" + device.dns + "</div></div>";
        html += "<div><div>MAC:</div><div>" + device.mac + "</div></div>";
        
        let device_stat = getDeviceStat(device);
        if( device_stat )
        {
            let dateTimeMsg = "";
            
            if( isOnline(device) )
            {
                dateTimeMsg = "Online";
            }
            else
            {
                let lastSeenTimestamp = Date.parse(device_stat["offline_since"]);
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

        services = {}
        Object.entries(device.services).forEach(function([key, value])
        {
            if( value == "http" ) value = {"value": value, "link": "http://" + device.dns };
            else if( value == "https" ) value = {"value": value, "link": "https://" + device.dns };
            
            services[key] = value;
        });
        
        html += showRows(services,"Services","rows");
        //html += showRows(device.ports,"Ports","rows");
        
        connection_data = {}
        wan_data = {}

        if( device.connection )
        {
            if( device.connection["vlans"] )
                connection_data["Vlan"] = "" + device.connection["vlans"];
            if( device.connection["target_interface"] && device.connection["type"] != "wifi" )
                connection_data["Port"] = device.connection["target_interface"];
            else
                connection_data["Port"] = "Wifi";
            
            let interface_stat = getInterfaceStat(device);
            if( interface_stat )
            {
                if( interface_stat["speed"] )
                {
                    let inSpeed = interface_stat["speed"]["in"];
                    let outSpeed = interface_stat["speed"]["out"];
                    
                    if( inSpeed != null )
                    {
                        let duplex = "";
                        if( "duplex" in interface_stat["details"] )
                        {
                            duplex += " - " + ( interface_stat["details"]["duplex"]["value"] == "full" ? "FullDuplex" : "HalfDuplex" );
                        }
                        
                        connection_data["Speed"] = { "value": formatSpeed(inSpeed) + (inSpeed == outSpeed ? '' : ' RX / ' + formatSpeed(outSpeed) + " TX" ) + duplex };
                    }
                }

                Object.entries(interface_stat["details"]).forEach(function([key, value])
                {
                    if( key == "duplex" )
                        return;
                                           
                    if( key == "wan_type" ) wan_data["type"] = value;
                    else if( key == "wan_state" ) wan_data["state"] = value;
                    else connection_data[key] = value;
                });

                if( interface_stat.traffic )
                {
                    let in_data = formatTraffic( interface_stat.traffic["in_avg"], true);
                    let out_data = formatTraffic( interface_stat.traffic["out_avg"], true);
                    connection_data["Traffic"] = { "value": "⇨ " + in_data + ", ⇦ " + out_data };
                }
            }
        }
        

        
        html += showRows(connection_data,"Network","rows");
        html += showRows(wan_data,"Wan","rows");

        device.gids.forEach(function(gid){
            let group = getGroup(gid);
            html += showRows(group["details"],group["type"],"rows");
        });

        if( device_stat )
        {
            Object.entries(device_stat["details"]).forEach(function([key, value])
            {
                let _value = value["value"];
                html += "<div><div>" + capitalizeFirstLetter(key) + ":</div><div>" + _value + "</div></div>";
            });
        }

        html += "</div>"
        
        mx.Tooltip.setText(html);

        // calculate font size
        let container = document.body.querySelector("svg .nodes rect");
        let box = container.getBoundingClientRect();
        let real_font_size = box.height * font_size / box_height;
        let real_max_width = box.width * 250 / box_width;
        
        if( real_font_size > 16 ) real_font_size = 16;
        
        let tooltip = mx.Tooltip.getRootElement();
        tooltip.style.fontSize = real_font_size + "px";
        tooltip.style.maxWidth = real_max_width + "px";

        // calculate column alignment
        let columns = tooltip.querySelectorAll("div.rows > div > div > div:first-child");
        let column_width = 0;
        columns.forEach(function(column)
        {
            let length = column.getBoundingClientRect().width;
            if( length > column_width ) column_width = length;
        });
        columns.forEach(function(column)
        {
            column.style.minWidth = column_width + "px";
        });
            
        link
            .classed("online", false)
            .classed("offline", false)
            .filter(l => l.source.data === d.data || l.target.data === d.data)
            .classed("online", isOnline(d.data.device))
            .classed("offline", !isOnline(d.data.device));
    }
        
    function toggleTooltip(d)
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
        
        let body_height = window.innerHeight;
        
        let top = nodeRect.top;
        if( top + tooltipRect.height > body_height ) 
        {
            top = body_height - tooltipRect.height - 6;
            arrowOffset = tooltipRect.height - ( body_height - ( nodeRect.top + nodeRect.height / 2 ) );
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
    
    function formatTraffic(traffic, format_zero)
    {
        if( traffic > 100000000 ) return Math.round( traffic / 1000000 ).toFixed(1) + " MB/s";                  // >= 100MB
        
        if( traffic > 1000000 ) return ( Math.round( ( traffic / 1000000 ) * 10 ) / 10 ).toFixed(1) + " MB/s";  // >= 1MB

        if( traffic > 100000 ) return Math.round( traffic / 1000 ).toFixed(1) + " KB/s";                        // >= 100KB
        
        if( traffic > 1000 ) return ( Math.round( ( traffic / 1000 ) * 10 ) / 10 ).toFixed(1) + " KB/s";        // >= 1KB
        
        if( traffic > 100 ) return ( Math.round(traffic / 100) / 10 ).toFixed(1) + " KB/s";
        
        return format_zero ? "0 KB/s" : null;
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
    
    function showRows(rows, name, cls)
    {
        let html = '';
        if( Object.entries(rows).length > 0)
        {
            html += "<div><div>" + capitalizeFirstLetter(name) + ":</div><div class='" + cls + "'><div>";
            Object.entries(rows).forEach(function([key, value])
            {
                [key, value] = formatDetails(key, value)

                if( !(value && typeof( value ) == "object") ) value = {"value": value}

                let _value = value["value"];
                if( value["format"] == "attenuation" ) 
                    _value += " db";
                
                html += "<div";
                
                if( value["link"] )
                    html += " class=\"link\" onclick=\"window.open('" + value["link"] + "', '_blank')\"";
                
                html += "><div>" + key + "</div><div>" + _value + "</div></div>";
            });
            html += "</div></div></div>";
        }
        return html;
    }

    return ret;
})( mx.D3 || {} );
