<?php
require "config.php";

require "../shared/libs/http.php";
require "../shared/libs/auth.php";
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

if( !Auth::hasGroup("admin") )
{
    HttpResponse::throwForbidden();
}

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/main/fonts/css/animation.css">
<link rel="stylesheet" href="/main/fonts/css/fontello.css">
<link rel="stylesheet" href="/main/css/shared_root.css">
<link rel="stylesheet" href="/main/css/shared_ui.css">
<link href="./ressources?type=css&version=<?php echo Ressources::getCSSVersion(__DIR__.'/css/'); ?>" rel="stylesheet">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="./ressources?type=components&version=<?php echo Ressources::getComponentVersion(__DIR__.'/components/'); ?>"></script>
<script src="/ressources?type=js"></script>
</head>
<body class="inline">
<script>
var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
if( theme ) document.body.classList.add(theme);

mx.SNCore = (function( ret ) {
  
    var daemonApiUrl = mx.Host.getBase() + 'api.php'; 
    var refreshDaemonStateTimer = 0;
    
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
    
    function setLoadingGear(job_started)
    {
        let date = new Date(job_started);
        let now = new Date();
        let duration = Math.floor( ( now.getTime() / 1000 - date.getTime() / 1000 ) * 10 ) / 10;
        
        let action = "<div class=\"detailView\" onclick=\"document.location.href='../update_system/'\">" + mx.I18N.get("Software check") + "</div>";
        
        document.body.innerHTML = "<div style=\"text-align: center\">" + mx.I18N.get("{1} is running since {2} seconds").fill({"1": action, "2": duration}) + " seconds</div>";
    }
    
    function processData(last_data_modified, changed_data)
    {
        if( changed_data.hasOwnProperty("software") )
        {   
            let content = "";
            
            if( !changed_data["software"].hasOwnProperty("states") )
            {
                content += "<div style=\"text-align: center\">";
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

                        console.log(dayDiff)
                        
                        let nowMinutes = now.getHours() * 60 + now.getMinutes();
                        let latestMinutes = latestDate.getHours() * 60 + latestDate.getMinutes();

                        console.log(nowMinutes + " " + latestMinutes)

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
                
                    content += "<div class=\"tooltip lastUpdate\">" + lastUpdate + lastUpdateDetails + "</div>";
                    
                    content += "</div>";
                }
            }
                
            content += "</div>";
                
            document.body.innerHTML = content;
        }
    }
        
    function handleDaemonState(state)
    {
        window.clearTimeout(refreshDaemonStateTimer);
        
        //console.log(state);
        
        if( state["job_is_running"] )
        {
            refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 1000);
        }
        else
        {
            refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
        }

        if( state["job_is_running"] && state["job_cmd_name"] == "software check" ) setLoadingGear(state["job_started"]);
        else if( Object.keys(state["changed_data"]).length > 0 ) processData(state["last_data_modified"], state["changed_data"] );
    }
    
    function refreshDaemonState(last_data_modified,callback)
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl);
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    handleDaemonState(response);
                    
                    if( callback ) callback();
                }
                else
                {
                    alert( response["message"] );
                }
            }
            else
            {
                console.log( this.response, "Code: " + this.status + ", Message: '" + this.statusText + "'" );
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(last_data_modified, callback) }, 15000);
            }
        };
        
        xhr.send(JSON.stringify({"action": "state", "parameter": { "type": "software", "last_data_modified": last_data_modified }}));
    }
    
    ret.startSoftwareCheck = function()
    {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", daemonApiUrl);
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;
            
            if( this.status == 200 ) 
            {
                var response = JSON.parse(this.response);
                if( response["status"] == "0" )
                {
                    handleDaemonState(response);
                }
                else
                {
                    alert(response["message"]);
                }
            }
            else
            {
                alert("Code: " + this.status + ", Message: '" + this.statusText + "'")
            }
        };
        
        xhr.send(JSON.stringify({"action": "refreshSoftwareVersionCheck"}));
    }
        
    ret.init = function()
    { 
        refreshDaemonState(null, function(){
            console.log("done");
        });            
    }
    
    ret.openUrl = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }
    
    return ret;
})( mx.SNCore || {} );
    
mx.OnDocReady.push( mx.SNCore.init );
</script>
</body>
</html>
