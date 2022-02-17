// mx.Menu needs to be defined in the beginning, because it is used during component initialisation
mx.Menu = (function( ret ) {
    var menuGroups = {};

    function processI18N( str, mainKey )
    {
        matches = str.matchAll(/{i18n_([^}]*)}/g);
        for (const match of matches) {
            str = str.replace(match[0],mx.I18N.get(match[1],mainKey));
        }
        return str;
    }

    function sortMenu(entries)
    {
        var keys = Object.keys(entries);
        
        keys.sort(function(a,b)
        {
            if( entries[a]['order'] < entries[b]['order'] ) return -1;
            if( entries[a]['order'] > entries[b]['order'] ) return 1;
            return 0;
        });
        
        var result = {};
        
        for( key in keys )
        {
            result[keys[key].toString()] = entries[keys[key]];
        }

        return result;
    }

    ret.getMainGroup = function(mainGroupId)
    {
        if(mainGroupId in menuGroups)
        {
            return menuGroups[mainGroupId]['_'];
        }
        else
        {
            console.error("MenuGroup '" + mainGroupId + "' not found");
        }
    };

    /*ret.getMainGroups = function()
    {
        return Object.values(menuGroups).map( entry => entry['_'] );
    };*/

    ret.addMainGroup = function(mainGroupId,order,title)
    {
        var mainGroup = menuGroups[mainGroupId] = {
            id:mainGroupId,
            order: order,
            title: title,
            subGroups: {},
            _: {
                getId: function(){ return mainGroupId; },
                getTitle: function(){ return mainGroup['title']; },
                getSubGroup: function(subGroupId){ return mainGroup['subGroups'][subGroupId]['_']; },
                //getSubGroups: function(){ return Object.values(mainGroup['subGroups']).map( entry => entry['_'] ); },
                addSubGroup: function(subGroupId,order,title,iconUrl){
                    var subGroup = mainGroup['subGroups'][subGroupId] = {
                        id:subGroupId, order: order, title: title, iconUrl: iconUrl,
                        menuEntries: {},
                        _: {
                            isEntry: function(){ return false; },
                            getId: function(){ return subGroupId; },
                            getTitle: function(){ return subGroup['title']; },
                            getMainGroup: function(){ return mainGroup['_']; },
                            getEntry: function(entryId){ return subGroup['menuEntries'].hasOwnProperty(entryId) ? subGroup['menuEntries'][entryId]['_'] : null; },
                            getEntries: function(){ return Object.values(subGroup['menuEntries']).map( entry => entry['_'] ); },
                            addUrl: function(entryId,url,usergroups,order,title,info,newWindow,iconUrl){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                var entries = subGroup['menuEntries'];
                                var entry = entries[entryId] = {
                                    id: entryId, order:order,usergroups:usergroups,type:'url',url:url,title:title,info:info,newWindow:newWindow, iconUrl: iconUrl,
                                    _: {
                                        isEntry: function(){ return true; },
                                        getType: function(){ return "url"; },
                                        getId: function(){ return entry['id']; },
                                        getOrder: function(){ return entry['order']; },
                                        getUserGroups: function(){ return entry['usergroups']; },
                                        getType: function(){ return entry['type']; },
                                        getSubGroup: function(){ return subGroup['_']; },
                                        getTitle: function(){ return entry['title']; },
                                        getInfo: function(){ return entry['info']; },
                                        getNewWindow: function(){ return entry['newWindow']; },
                                        getIconUrl: function(){ return entry['iconUrl']; },
                                        getUrl: function(){ return entry['url']; }
                                    }
                                };
                            },
                            addHtml: function(entryId,html,callback,usergroups,order){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                var entries = subGroup['menuEntries'];
                                var entry = entries[entryId] = {
                                    id: entryId, order:order,usergroups:usergroups,type:'html',html:html,callback:callback,
                                    _: {
                                        isEntry: function(){ return true; },
                                        getType: function(){ return "html"; },
                                        getId: function(){ return entry['id']; },
                                        getOrder: function(){ return entry['order']; },
                                        getUserGroups: function(){ return entry['usergroups']; },
                                        getType: function(){ return entry['type']; },
                                        getSubGroup: function(){ return subGroup['_']; },
                                        getHtml: function(){ return entry['html']; },
                                        getCallback: function(){ return entry['callback']; }
                                    }
                                };
                            }
                        }
                    };
                    return subGroup['_'];
                }
            }
        };

        return mainGroup['_'];
    };

    ret.buildMenu = function(subGroup, callback)
    {
        var entries = [];
        var callbacks = [];

        var menuEntries = subGroup.getEntries();
        var currentIndex = 1;
        
        var lastOrder = Math.max.apply(Math, menuEntries.map(function(o) { return o.getOrder(); }));

        var hasGroups = lastOrder && Math.floor(menuEntries[0].getOrder()/100) != Math.floor(lastOrder/100);
        
        if( hasGroups ) entries.push('<div class="group">')
        
        for(var i = 0; i < menuEntries.length; i++)
        {
            var entry = menuEntries[i];
            
            if( !entry.getUserGroups() || !mx.User.memberOf( entry.getUserGroups() ) )
            {
                continue;
            }

            var index = Math.floor(entry.getOrder()/100);
            
            if( currentIndex != index )
            {
                entries.push('</div><div class="group">');
                currentIndex = index;
            }
            
            if( entry.getType() == 'html' )
            {
                entries.push(entry.getHtml());
                callbacks.push(entry.getCallback());
            }
            else
            {
                var html = '<div class="service button ' + i + '" onClick="mx.Actions.openEntryById(event,\'' + subGroup.getMainGroup().getId() + '\',\'' + subGroup.getId() + '\',\'' + entry.getId() + '\')">';
                html += '<div>';
                if( entry.getIconUrl() ) html += '<svg viewBox="0 0 20 20"><use xlink:href="/main/icons/' + entry.getIconUrl() + '#icon" /></svg>';
                //if( entry.getIconUrl() ) html += '<img src="/main/icons/' + entry.getIconUrl() + '"/>';
                html += '<div>' + entry.getTitle() + '</div>';
                html += '</div><div>' + entry.getInfo() + '</div></div>';
                
                entries.push(html);
            }
        }
        
        if( hasGroups ) entries.push('</div>')

        callback(entries.join(""),callbacks);
    };

    ret.init = function()
    {
        // needs to work with keys directly, because this is the post processing part of the data
        for( mainKey in menuGroups )
        {
            var mainGroup = menuGroups[mainKey];
            
            var match = mainGroup['title'].match(/{i18n_([^}]*)}/);
            if( match !== null ) mainGroup['title'] = mainGroup['title'].replace(match[0],mx.I18N.get(match[1],mainKey));

            for( subKey in mainGroup['subGroups'] )
            {
                var subGroup = mainGroup['subGroups'][subKey];

                subGroup['title'] = processI18N(subGroup['title'],mainKey);

                for( entryKey in subGroup['menuEntries'] )
                {
                    var entry = subGroup['menuEntries'][entryKey];

                    if( entry['type'] === 'url' )
                    {
                        if( entry['title'] ) entry['title'] = processI18N(entry['title'],mainKey+'_'+subKey);
                        if( entry['info'] ) entry['info'] = processI18N(entry['info'],mainKey+'_'+subKey);

                        match = entry['url'].match(/(\/\/)([^\.]*)\.({host})/);
                        if( match !== null ) entry['url'] = entry['url'].replace('//' + match[2] + "." + match[3], "//" + mx.Host.getAuthPrefix() + match[2] + "." + mx.Host.getDomain() );
                    }
                    else
                    {
                        entry['html'] = processI18N(entry['html'],mainKey+'_'+subKey);
                    }
                }
            }
        }

        var template = mx.$('#menuTemplate');

        var _menuGroups = sortMenu( menuGroups );
        for( index in _menuGroups )
        {
            var mainGroup = _menuGroups[index];
            
            if( mainGroup['id'] == 'home' ) continue;
            
            var subGroupStates = {}
            
            var _subGroups = sortMenu( mainGroup['subGroups'] );

            for( index in _subGroups )
            {
                var subGroup = _subGroups[index];
                
                var hasEntries = false;
                for( entryKey in subGroup['menuEntries'] )
                {
                    var entry = subGroup['menuEntries'][entryKey];
                    
                    if( entry['usergroups'] && mx.User.memberOf( entry['usergroups'] ) )
                    {
                        hasEntries = true;
                        break;
                    }
                }
                
                subGroupStates[subGroup['id']] = hasEntries
            }
            
            if( Object.values(subGroupStates).filter(value => value).length == 0 ) continue;
            
            var menuDiv = template.cloneNode(true);
            menuDiv.setAttribute('id',mainGroup['id']);
            menuDiv.querySelector('.header').innerHTML = mainGroup['title'];
            menuDiv.style.display = "";
            template.parentNode.appendChild(menuDiv);

            var buttonTemplate = menuDiv.querySelector('.service.button');
            menuDiv.removeChild(buttonTemplate);

            for( index in _subGroups )
            {
                var subGroup = _subGroups[index];
                
                if( !subGroupStates[subGroup['id']] ) continue;

                var button = buttonTemplate.cloneNode(true);
                button.setAttribute("id", mainGroup['id'] + '-' + subGroup['id'] );
                button.setAttribute("onClick","mx.Actions.openMenuById(event,'" + mainGroup['id'] + "','" + subGroup['id'] + "');");
                //button.firstChild.innerHTML = subGroup['iconUrl'] ? '<img src="/main/icons/' + subGroup['iconUrl'] + '"/>' : '';
                button.firstChild.innerHTML = subGroup['iconUrl'] ? '<svg viewBox="0 0 20 20"><use xlink:href="/main/icons/' + subGroup['iconUrl'] + '#icon" /></svg>' : '';
                button.lastChild.innerHTML = subGroup['title'];
                menuDiv.appendChild(button);

                subGroup['menuEntries'] = sortMenu( subGroup['menuEntries'] );
            }
        }
    };

    ret.addMainGroup('home', -1, 'Home').addSubGroup('home', -1, 'Home');
    ret.addMainGroup('workspace', 1000, '{i18n_Workspace}');
    ret.addMainGroup('automation', 2000, '{i18n_Automation}');

    var mainGroup = ret.addMainGroup('admin', 3000, '{i18n_Admin}');
    mainGroup.addSubGroup('tools', 200, '{i18n_Tools}', 'core_tools.svg');
    mainGroup.addSubGroup('system', 300, '{i18n_System}', 'core_system.svg');
    mainGroup.addSubGroup('devices', 400, '{i18n_Devices}', 'core_devices.svg');

    return ret;
})( mx.Menu || {} ); 
