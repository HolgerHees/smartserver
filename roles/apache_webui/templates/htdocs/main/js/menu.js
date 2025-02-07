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
        let keys = Object.keys(entries);
        
        keys.sort(function(a,b)
        {
            if( entries[a]['options']['order'] < entries[b]['options']['order'] ) return -1;
            if( entries[a]['options']['order'] > entries[b]['options']['order'] ) return 1;
            return 0;
        });
        
        let result = {};
        
        for( key in keys )
        {
            result[keys[key].toString()] = entries[keys[key]];
        }

        return result;
    }

    function filterAllowedEntries(entries)
    {
        return entries.filter(entry => entry.getUserGroups() && mx.User.memberOf( entry.getUserGroups() ));
    }
    
    function filterMenuEntries(subGroup)
    {
        return subGroup.isSingleEntryGroup() ? [] : subGroup.getEntries().filter(entry => entry.getTitle() );
    }

    ret.checkMenu = function(mainGroupId, subGroupId, entryId)
    {
        return mainGroupId in menuGroups && subGroupId in menuGroups[mainGroupId]['subGroups'] && entryId in menuGroups[mainGroupId]['subGroups'][subGroupId]["menuEntries"];
    };

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

    ret.addMainGroup = function(mainGroupId, options = {})
    {
        let mainGroup = menuGroups[mainGroupId] = {
            id:mainGroupId,
            uid: mainGroupId,
            options: options,
            subGroups: {},
            _: {
                getId: function(){ return mainGroup['id']; },
                getUId: function(){ return mainGroup['uid']; },
                getType: function(){ return "group"; },
                getTitle: function(){ return mainGroup['options']['title']; },
                getSubGroup: function(subGroupId){ return mainGroup['subGroups'][subGroupId]['_']; },
                //getSubGroups: function(){ return Object.values(mainGroup['subGroups']).map( entry => entry['_'] ); },
                //addSubGroup: function(subGroupId, order, title, icon){
                addSubGroup: function(subGroupId, options = {}){
                    let subGroup = mainGroup['subGroups'][subGroupId] = {
                        id:subGroupId, uid: mainGroup['uid'] + "-" + subGroupId, options: options,
                        menuEntries: {},
                        _: {
                            getId: function(){ return subGroup['id']; },
                            getUId: function(){ return subGroup['uid']; },
                            getType: function(){ return "subgroup"; },
                            getTitle: function(){ return subGroup['options']['title']; },
                            getIconUrl: function(){ return subGroup['options']['icon']; },
                            getMainGroup: function(){ return mainGroup['_']; },
                            getEntry: function(entryId){ return subGroup['menuEntries'].hasOwnProperty(entryId) ? subGroup['menuEntries'][entryId]['_'] : null; },
                            getEntries: function(){ return filterAllowedEntries(Object.values(subGroup['menuEntries']).map( entry => entry['_'] )); },
                            isSingleEntryGroup: function(){ return Object.values(subGroup['menuEntries']).length == 1; },
                            getMenuEntries: function(){ return filterMenuEntries(subGroup['_']) },
                            addUrl: function(entryId, groups, url, options = {}){
                            //addUrl: function(entryId, url, usergroups, order = 0, title = null, info = null, icon = null, options = {}){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                let entries = subGroup['menuEntries'];
                                let entry = entries[entryId] = {
                                    id: entryId, uid: subGroup['uid'] + "-" + entryId, groups:groups, type: 'url', url:url, options: options,
                                    _: {
                                        getId: function(){ return entry['id']; },
                                        getUId: function(){ return entry['uid']; },
                                        getType: function(){ return "entry"; },
                                        getUserGroups: function(){ return entry['groups']; },
                                        getContentType: function(){ return entry['type']; },
                                        getUrl: function(){ return entry['url']; },

                                        getSubGroup: function(){ return subGroup['_']; },

                                        getOrder: function(){ return entry['options']['order']; },
                                        getTitle: function(){ return entry['options']['title']; },
                                        getInfo: function(){ return entry['options']['info']; },
                                        getIconUrl: function(){ return entry['options']['icon']; },

                                        getCallbacks: function(){ return entry['options']['callbacks']; },

                                        //getUrl: function(){ return typeof entry['url'] === 'object' ? entry['url']['callback'](entry['url']['url']) : entry['url']; },

                                        getNewWindow: function(){ return entry['options']['target'] ? entry['options']['target'] == '_blank' : false; },
                                        isLoadingGearEnabled: function(){ return 'loading_gear' in entry['options'] ? entry['options']['loading_gear'] : true; },
                                    }
                                };
                            },
                            addHtml: function(entryId, groups, html, options = {}){
                            //addHtml: function(entryId, html, callbacks, usergroups, order = 0, title = null, info = null, icon = null){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                if( typeof callbacks == 'function' ) callbacks = {"post": [ callbacks ] };
                                let entries = subGroup['menuEntries'];
                                let entry = entries[entryId] = {
                                    id: entryId, uid: subGroup['uid'] + "-" + entryId, groups:groups, type:'html', html:html, options: options,
                                    _: {
                                        getId: function(){ return entry['id']; },
                                        getUId: function(){ return entry['uid']; },
                                        getType: function(){ return "entry"; },
                                        getUserGroups: function(){ return entry['groups']; },
                                        getContentType: function(){ return entry['type']; },
                                        getHtml: function(){ return entry['html']; },

                                        getSubGroup: function(){ return subGroup['_']; },

                                        getOrder: function(){ return entry['options']['order']; },
                                        getTitle: function(){ return entry['options']['title']; },
                                        getInfo: function(){ return entry['options']['info']; },
                                        getIconUrl: function(){ return entry['options']['icon']; },

                                        getCallbacks: function(){ return entry['options']['callbacks']; },

                                        //isLoadingGearEnabled: function(){ return true; }
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
    
    function buildMainMenu()
    {
        // needs to work with keys directly, because this is the post processing part of the data
        for( mainKey in menuGroups )
        {
            let mainGroup = menuGroups[mainKey];
            
            let match = mainGroup['options']['title'].match(/{i18n_([^}]*)}/);
            if( match !== null ) mainGroup['options']['title'] = mainGroup['options']['title'].replace(match[0],mx.I18N.get(match[1],mainKey));

            for( subKey in mainGroup['subGroups'] )
            {
                let subGroup = mainGroup['subGroups'][subKey];

                subGroup['options']['title'] = processI18N(subGroup['options']['title'],mainKey);

                for( entryKey in subGroup['menuEntries'] )
                {
                    let entry = subGroup['menuEntries'][entryKey];

                    if( entry['options']['title'] ) entry['options']['title'] = processI18N(entry['options']['title'],mainKey+'_'+subKey);
                    if( entry['options']['info'] ) entry['options']['info'] = processI18N(entry['options']['info'],mainKey+'_'+subKey);

                    if( entry['type'] === 'url' )
                    {
                        let reference = entry;
                        if( typeof reference['url'] === "object" ) reference = reference['url'];
                        match = reference['url'].match(/(\/\/)([^\.]*)\.({host})/);
                        if( match !== null ) reference['url'] = reference['url'].replace('//' + match[2] + "." + match[3], "//" + mx.Host.getAuthPrefix() + match[2] + "." + mx.Host.getDomain() );
                    }
                    else
                    {
                        entry['html'] = processI18N(entry['html'],mainKey+'_'+subKey);
                    }
                }
            }
        }

        let groupTemplate = document.createElement("div");
        groupTemplate.classList.add("group");
        groupTemplate.innerHTML = '<div class="header"></div>';
        
        let rowTemplate = document.createElement("div");
        rowTemplate.classList.add("row");
        rowTemplate.innerHTML = '<div class="service button"><div></div><div></div></div><div class="submenu"></div>'

        let menuElement = mx.$("#menu .main");

        let _menuGroups = sortMenu( menuGroups );
        for( index in _menuGroups )
        {
            let mainGroup = _menuGroups[index];
            
            if( mainGroup['id'] == 'home' ) continue;
            
            let subGroupStates = {}
            
            let _subGroups = sortMenu( mainGroup['subGroups'] );

            for( index in _subGroups )
            {
                let subGroup = _subGroups[index];
                
                let hasEntries = false;
                for( entryKey in subGroup['menuEntries'] )
                {
                    let entry = subGroup['menuEntries'][entryKey];
                    
                    if( entry['groups'] && mx.User.memberOf( entry['groups'] ) )
                    {
                        hasEntries = true;
                        break;
                    }
                }
                
                subGroupStates[subGroup['id']] = hasEntries
            }
            
            if( Object.values(subGroupStates).filter(value => value).length == 0 ) continue;
            
            let menuDiv = groupTemplate.cloneNode(true);
            menuDiv.setAttribute('id',mainGroup['id']);
            menuDiv.querySelector('.header').innerHTML = mainGroup['options']['title'];
            menuDiv.style.display = "";
            
            menuElement.appendChild(menuDiv);

            for( index in _subGroups )
            {
                let subGroup = _subGroups[index];
                
                if( !subGroupStates[subGroup['id']] ) continue;

                let row = rowTemplate.cloneNode(true);
                let button = row.querySelector(".button");
                button.setAttribute("id", subGroup['uid'] );
                button.setAttribute("onClick","mx.Actions.openMenuById(event,'" + subGroup['uid'] + "');");
                //button.firstChild.innerHTML = subGroup['iconUrl'] ? '<img src="/main/icons/' + subGroup['iconUrl'] + '"/>' : '';
                button.firstChild.innerHTML = subGroup['options']['icon'] ? '<svg viewBox="0 0 16 16"><use xlink:href="/main/icons/' + subGroup['options']['icon'] + '#icon" /></svg>' : '';
                button.lastChild.innerHTML = subGroup['options']['title'];
                menuDiv.appendChild(row);

                subGroup['menuEntries'] = sortMenu( subGroup['menuEntries'] );
                
                let submenu = row.querySelector(".submenu")
                submenu.setAttribute("id", subGroup['uid'] + "-submenu" );
            }
        }
    }
    
    function buildSubMenu(element, subGroup)
    {
        let currentIndex = -1;
        let submenuButtonTemplate = document.createElement("div");
        submenuButtonTemplate.classList.add("service");
        submenuButtonTemplate.classList.add("button");
        submenuButtonTemplate.innerHTML = "<div></div><div></div>";
        
        let menuEntries = subGroup.getMenuEntries();
        
        for( entryKey in menuEntries )
        {
            let entry = subGroup.getEntries()[entryKey];
            
            let index = Math.floor(entry.getOrder()/100);
            
            if( currentIndex != index )
            {
                if( currentIndex != -1 )
                {
                    let separator = document.createElement("div");
                    separator.classList.add("separator");
                    element.appendChild(separator);
                }
                currentIndex = index;
            }
            
            let submenuButton = submenuButtonTemplate.cloneNode(true);
            submenuButton.setAttribute("id", entry.getUId() );
            submenuButton.setAttribute("onClick","mx.Actions.openEntryById(event,'" + entry.getUId() + "');");
            submenuButton.firstChild.innerHTML = entry.getIconUrl() ? '<svg viewBox="0 0 16 16"><use xlink:href="/main/icons/' + entry.getIconUrl() + '#icon" /></svg>' : '';
            submenuButton.lastChild.innerHTML = entry.getTitle();
            element.appendChild(submenuButton);
        }
    }

    function pushEntry(entries, callbacks, currentIndex, entry, html, _callbacks)
    {
        let index = Math.floor(entry.getOrder()/100);

        if( currentIndex != index )
        {
            if( currentIndex != -1 )
            {
                entries.push('</div><div class="group">');
            }
            currentIndex = index;
        }

        entries.push(html);

        if( _callbacks )
        {
            if( _callbacks["post"] ) callbacks["post"] = callbacks["post"].concat(_callbacks["post"]);
            if( _callbacks["init"] ) callbacks["init"] = callbacks["init"].concat(_callbacks["init"]);
        }

        return currentIndex
    }
        
    ret.buildContentSubMenu = function(subGroup)
    {
        let entries = [];
        let callbacks = {"post":[],"init":[]};

        let menuEntries = subGroup.getEntries();
        let currentIndex = -1;
        
        let lastOrder = Math.max.apply(Math, menuEntries.map(function(o) { return o.getOrder(); }));

        let hasGroups = lastOrder && Math.floor(menuEntries[0].getOrder()/100) != Math.floor(lastOrder/100);
        
        if( hasGroups ) entries.push('<div class="group">')
        
        for(let i = 0; i < menuEntries.length; i++)
        {
            let entry = menuEntries[i];

            if(entry.getTitle())
            {
                let html = '<div class="service button ' + i + '" onClick="mx.Actions.openEntryById(event,\'' + entry.getUId() + '\')">';
                html += '<div>';
                if( entry.getIconUrl() ) html += '<svg viewBox="0 0 20 20"><use xlink:href="/main/icons/' + entry.getIconUrl() + '#icon" /></svg>';
                //if( entry.getIconUrl() ) html += '<img src="/main/icons/' + entry.getIconUrl() + '"/>';
                html += '<div>' + entry.getTitle() + '</div>';
                html += '</div><div>' + entry.getInfo() + '</div></div>';

                currentIndex = pushEntry(entries, callbacks, currentIndex, entry, html, null);
            }
            else if( entry.getContentType() == 'html' )
            {
                currentIndex = pushEntry(entries, callbacks, currentIndex, entry, entry.getHtml(), entry.getCallbacks());
            }
        }
        
        if( hasGroups ) entries.push('</div>')

        return { 'content': entries.join(""), 'callbacks': callbacks };
    };
    
    ret.activateMenu = function(entry)
    {
        let lastActiveElement = mx.$(".service.active");
        let lastActiveElementId = lastActiveElement ? lastActiveElement.id : null;
        
        let activeElementId = null;
        let activeSubmenuElementId = null;
        let activeSubGroup = null;
        
        if( entry )
        {
            activeSubGroup = entry.getType() == "subgroup" ? entry : entry.getSubGroup()
            if( activeSubGroup.getMenuEntries().length == 0 )
            {
                activeElementId = activeSubGroup.getUId();
            }
            else
            {
                activeSubmenuElementId = activeSubGroup.getUId() + "-submenu";
                activeElementId = entry.getUId();
                
            }
        }
        
        if( activeSubmenuElementId )
        {
            let activeSubmenuElement = mx.$("#" + activeSubmenuElementId);
            if( activeSubmenuElement.innerHTML == "" )
            {
                buildSubMenu(activeSubmenuElement, activeSubGroup);

                activeSubmenuElement.style.display = "block";
                window.setTimeout(function(){ 
                    activeSubmenuElement.style.maxHeight = activeSubmenuElement.scrollHeight + "px";
                    
                    window.setTimeout(function(){
                        let mainMenuElement = mx.$("#menu .main");
                        let mainRect = mainMenuElement.getBoundingClientRect();
                        let mainOffset = mx.Core.getOffsets(mainMenuElement);
                        let mainBottomPos = mainRect.height + mainOffset.top + mainMenuElement.scrollTop;
                        
                        let subRect = activeSubmenuElement.getBoundingClientRect();
                        let subOffsets = mx.Core.getOffsets(activeSubmenuElement);
                        let subBottomPos = subOffsets.top + subRect.height;

                        if( subBottomPos > mainBottomPos )
                        {
                            let scrollTop = 0;
                            if( subRect.height > mainRect.height )
                            {
                                let groupRect = mx.$("#" + activeElementId).getBoundingClientRect();
                                scrollTop = mainMenuElement.scrollTop + ( groupRect.top - mainRect.top );
                            }
                            else
                            {
                                scrollTop = mainMenuElement.scrollTop + ( subBottomPos - mainBottomPos ) + 100;
                            }

                            mainMenuElement.scrollTo({
                                top: scrollTop,
                                behavior: 'smooth'
                            });
                        }
                    },350);
                },0);
            }
            // needed to toggle submenu
            else if( entry.getType() == "subgroup" && lastActiveElementId == activeElementId )
            {
                activeSubmenuElementId = null;
            }
        }

        if( lastActiveElementId != activeElementId)
        {
            if(lastActiveElement) lastActiveElement.classList.remove("active");
            if( activeElementId ) // activeElementId is null for home
            {
                let element = document.getElementById(activeElementId);
                element.classList.add("active");
            }
        }
        
        mx.$$("#menu .group .submenu").forEach(function(element)
        {
            if( element.id != activeSubmenuElementId && element.style.display != "" )
            {
                element.style.maxHeight = "";
                window.setTimeout(function(){ 
                    element.style.display=""; 
                    element.innerHTML = "";
                },300);
            }
        });

    }

    ret.init = function()
    {
        buildMainMenu();
    };

    ret.addMainGroup('home', { 'order': -1, 'title': 'Home' }).addSubGroup('home', { 'order': -1, 'title': 'Home' });
    ret.addMainGroup('workspace', { 'order': 1000, 'title': '{i18n_Workspace}' });
    ret.addMainGroup('automation', { 'order': 2000, 'title': '{i18n_Automation}' });

    let mainGroup = ret.addMainGroup('admin', { 'order': 3000, 'title': '{i18n_Admin}' });
    mainGroup.addSubGroup('tools', { 'order': 200, 'title': '{i18n_Tools}', 'icon': 'core_tools.svg' });
    mainGroup.addSubGroup('system', { 'order': 300, 'title': '{i18n_System}', 'icon': 'core_system.svg' });
    mainGroup.addSubGroup('devices', { 'order': 400, 'title': '{i18n_Devices}', 'icon': 'core_devices.svg' });

    return ret;
})( mx.Menu || {} ); 
