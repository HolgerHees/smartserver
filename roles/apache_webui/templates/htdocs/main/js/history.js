mx.History = (function( ret ) {
    ret.addMenu = function(subGroup)
    {
        if( subGroup )
        {
            if( history.state && history.state['subGroupId'] == subGroup.getId() && history.state['entryId'] == null )
            {
                return;
            }
            else
            {
                var mainGroup = subGroup.getMainGroup();
                name = mainGroup.getTitle() + "/" + subGroup.getTitle();
                
                var stateObj = { mainGroupId: mainGroup.getId(), subGroupId: subGroup.getId(), entryId: null, url: null };
                history.pushState(stateObj, name, '?ref=' + mainGroup.getId() + '|' + subGroup.getId() );
            }
        }
        else
        {
            if( history.state && history.state['subGroupId'] == null )
            {
                return;
            }
            else
            {
                var stateObj = { mainGroupId: null, subGroupId: null, entryId: null, url: null };
                history.pushState(stateObj, 'Home', document.location.origin );
            }
        }
    };
    ret.addEntry = function(entry,url)
    {
        if( history.state && history.state['entryId'] == entry.getId() && history.state['url'] == url )
        {
            return;
        }
        else
        {
            var subGroup = entry.getSubGroup();
            var mainGroup = subGroup.getMainGroup();
            
            var ref =  mainGroup.getId() + '|' + entry.getSubGroup().getId() + '|' + entry.getId();
            if( url ) ref += '|' + encodeURIComponent(url);

            var stateObj = { mainGroupId: mainGroup.getId(), subGroupId: subGroup.getId(), entryId: entry.getId(), url: url };
            history.pushState(stateObj, entry.getTitle(), '?ref=' + ref );
        }
    };    
    ret.init = function(callback)
    {
        window.addEventListener("popstate", function(event) {
            //console.log(event);
            
            if( event.state )
            {
                var mainGroup;
                var subGroup;
                var entry;
                var url;
                
                if( event.state['subGroupId'] )
                {
                    mainGroup = mx.Menu.getMainGroup(event.state['mainGroupId']);
                    subGroup = mainGroup.getSubGroup(event.state['subGroupId']);

                    if( event.state['entryId'] )
                    { 
                        entry = subGroup.getEntry(event.state['entryId']);
                        url = event.state['url'];
                    }
                }
                
                callback(mainGroup,subGroup,entry,url);
            }
            else
            {
                console.log("mx.History blocked"); 
                mx.History.addMenu();
            }

            event.preventDefault();
        });
        
        if( history.state == null )
        {
            history.pushState(null, '', '?-' );
        }

        //console.log("mx.History init"); 
    };
        
    return ret;
})( mx.History || {} );
