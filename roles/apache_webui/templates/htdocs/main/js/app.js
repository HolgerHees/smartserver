mx.App = (function( ret ) {
    ret.checkDeeplink = function(ref)
    {
        if( ref ) 
        {
            var parts = ref.split(/%7C|\|/);
            var subMenuGroup = mx.Menu.getMainGroup(parts[0]).getSubGroup(parts[1]);
            if( parts.length > 2 )
            {
                var entry = subMenuGroup.getEntry(parts[2]);
                if( entry )
                {
                    mx.Actions.openEntry(entry, parts.length > 3 ? decodeURIComponent( parts[3] ) : null );
                }
                else
                {
                    mx.Actions.showError("notfound",ref);
                }
            }
            else
            {
                mx.Actions.openMenu(subMenuGroup);
            }
            return true;
        }
        
        return false;
    };
    
    ret.initInfoLayer = function()
    {
        var divLayer = mx.$("#info");
        var infoLayer = mx.$("#info .info");
        var hintLayer = mx.$("#info .hint");
        var progressLayer = mx.$("#info .progress");

        function showInfo(animated,info,hint)
        {
            infoLayer.innerHTML = info;
            hintLayer.innerHTML =  hint ? hint : "&nbsp;";
            hintLayer.style.visibility = hint ? "" : "hidden";
            
            divLayer.style.display = "flex";
            if( animated )
            {
                window.setTimeout(function(){ divLayer.style.backgroundColor = "rgba(0,0,0,0.5)"; }, 0);
            }
            else
            {
                divLayer.style.backgroundColor = "rgba(0,0,0,0.5)";
            }
        }
        
        function hideInfo(animated)
        {
            if( animated )
            {
                mx.Core.waitForTransitionEnd(divLayer, function(){ divLayer.style.display = ""; },"Info closed");
            }
            else
            {
                divLayer.style.display = "";
            }
            divLayer.style.backgroundColor = "rgba(0,0,0,0)";
        }
        
        mx.State.init(function(connectionState,animated)
        {
            //console.log("STATE: " + connectionState );
            
            if( connectionState == mx.State.SUSPEND )
            {
                showInfo(animated,mx.I18N.get("APP Suspend"),mx.I18N.get("tap to resume"));
            }
            else if( connectionState == mx.State.OFFLINE )
            {
                showInfo(animated,mx.I18N.get("Internet Offline"));
            }
            else if( connectionState == mx.State.ONLINE || connectionState == mx.State.UNREACHABLE || connectionState == mx.State.REACHABLE )
            {
                showInfo(animated,mx.I18N.get("Server Offline"));
            }
            else if( connectionState == mx.State.UNAUTHORIZED )
            {
                showInfo(animated,"");
            }
            else
            {
                hideInfo(animated);
            }
        }, function(inProgress)
        {
            progressLayer.style.visibility = inProgress ? "visible" : "";
        });
    };
    
    return ret;
})( mx.App || {} ); 
