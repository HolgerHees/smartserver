mx.SoftwareVersionsTemplates = (function( ret ) {
    let outdatedProcessData = null;
    let outdatedRoleData = null;
  
    var stateIcons = {
        "docker": "icon-inbox",
        "github": "icon-git",
        "opensuse": "icon-desktop",
        "fedora": "icon-desktop"
    }
    
    function formatVersion(version)
    {
        // git hashes
        if( version.length > 20 ) return version.substr(0,7);
        
        return version;
    }
    
    function formatDatetime(date)
    {
        let str = date.toLocaleString();
        str = str.substring(0,str.length - 3);
        return str;
    }

    ret.setLoadingGear = function(job_started)
    {
        let date = new Date(job_started);
        let now = new Date();
        let duration = Math.round( ( now.getTime() - date.getTime() )  / 1000 );
        
        let action_1 = "<div class=\"detailView\" onclick=\"document.location.href='../system/'\">";
        let action_2 = "</div>";
        
        let msg = mx.I18N.get("{1}Software check{2} is running since {3} {4}").fill({"1": action_1, "2": action_2, "3": duration, "4": mx.I18N.get( duration == 1 ? "second" : "seconds" ) })
        
        document.body.innerHTML = "<div class=\"is_running\">" + msg + "</div>";
    }
    
    ret.processData = function(last_data_modified, changed_data)
    {
        if( changed_data.hasOwnProperty("software") )
        {   
            let content = "";
            
            if( !changed_data["software"].hasOwnProperty("states") )
            {
                content += "<div class=\"not_available\">";
                content += mx.I18N.get("No software versions have been checked so far") + "<br><br><div class=\"form button\" onclick=\"mx.SNCore.startSoftwareCheck()\">" + mx.I18N.get("Start initial run") + "</div>";
              
            }
            else
            {
                let date = last_data_modified["software"] ? new Date(last_data_modified["software"] * 1000) : null;;
                let lastUpdateDateFormatted = date ? formatDatetime(date) : null;
              
                let states = changed_data["software"]["states"];
              
                content += "<div class=\"form table\">";
                content += "<div class=\"row\">";
                content += "<div>" + states.length + "</div>";
                content += "<div>Name</div>";
                content += "<div>Version</div>";
                content += "<div>Updates</div>";
                content += "<div>" + lastUpdateDateFormatted + "</div>";
                content += "</div>";
                
                states = states.sort(function(a,b){ return a["name"].localeCompare(b["name"]); });
                
                for( let index in states)
                { 
                    let state = states[index];
                    
                    let cls = "green";
                    if( state["updates"].length > 0 )
                    {
                        cls = "yellow";
                        for( let i = 0; i < state["updates"].length; i++)
                        {
                            if( state["current"]["branch"] == state["updates"][i]["branch"] )
                            {
                                cls = "red";
                                break;
                            }
                        }
                    }
                    
                    let icon = state["type"] in stateIcons ? stateIcons[state["type"]] : "";

                    content += "<div class=\"row " + cls + "\">";
                    content += "<div class=\"typeLink\" onClick=\"mx.SNCore.openUrl(event,'" + state["url"] + "')\"><span class=\"" + icon + "\"></span></div>";
                    content += "<div>" + state["name"] + "</div>";
                
                    let latestDate = new Date( state["current"]["date"] );

                    content += "<div class=\"tooltip\">" + formatVersion(state["current"]["version"]) + " <span class=\"hover\">Version " + formatVersion(state["current"]["version"]) + " from " + formatDatetime(latestDate) + "</span></div>";

                    let upgradesHTML = "";
                    let lastUpdate = "";
                    let lastUpdateDetails = "";
                    
                    if( state["updates"].length > 0)
                    {
                        let updates = state["updates"];
                        updates.sort(function(first, second) {
                            ( ( second["version"] == first["version"] ) ? 0 : ( ( second["version"] > first["version"] ) ? 1 : -1 ) );
                        });
                        
                        latestDate = null;
                        let upgradesHTML_r = [];
                        for( let i = 0; i < state["updates"].length; i++)
                        {
                            let update = state["updates"][i];
                        
                            let date = new Date( update["date"] );
                            //let dateFmt = date.toLocaleString();                      
                            if( latestDate == null || latestDate.getTime() < date.getTime() ) latestDate = date;

                            let current_branch = state["current"]["branch"] == update["branch"];
                            
                            if( update["url"] )
                            {
                                upgradesHTML_r.push("<div class=\"versionLink" + ( current_branch ? " currentBranch" : "" ) + "\" onClick=\"mx.SNCore.openUrl(event,'" + update["url"] + "')\"><span>" + formatVersion( update["version"] ) + "</span><span class=\"icon-export\"></span></div>");
                            }
                            else
                            {
                                upgradesHTML_r.push("<div class=\"" + ( current_branch ? " currentBranch" : "" ) + "\"><span>" + formatVersion( update["version"] ) + "</span></div>");
                            }
                        }
                        upgradesHTML = upgradesHTML_r.join(", ");
                        
                        let now = new Date();

                        let diff = ( now.getTime() / 1000 ) - (latestDate.getTime() / 1000);
                        
                        let dayDiff = Math.floor(diff / (60 * 60 * 24));

                        let nowMinutes = now.getHours() * 60 + now.getMinutes();
                        let latestMinutes = latestDate.getHours() * 60 + latestDate.getMinutes();

                        if( nowMinutes < latestMinutes )
                        {
                            dayDiff++;
                        }
                        
                        if( dayDiff <= 1)
                        {
                            let lastUpdate = ( dayDiff == 0 ? 'Today' : 'Yesterday' ) + " " + formatDatetime(latestDate);
                        }
                        else
                        {
                            if( dayDiff > 30 )
                            {
                                lastUpdate = latestDate.toLocaleDateString();
                            }
                            else
                            {
                                lastUpdate = dayDiff + " days ago";
                            }
                        }
                        
                        lastUpdate = "<span class=\"default\">" + lastUpdate + "</span>";
                        lastUpdateDetails = "<span class=\"hover\">" +  formatDatetime(latestDate) + "</span>";
                    }
                    
                    content += "<div>" + upgradesHTML + "</div>";
                
                    content += "<div class=\"software tooltip lastUpdate\">" + lastUpdate + lastUpdateDetails + "</div>";
                    
                    content += "</div>";
                }
            }
                
            content += "</div>";
                
            document.body.querySelector(".list").innerHTML = content;
        }
    }
    
    return ret;
})( mx.SoftwareVersionsTemplates || {} ); 
