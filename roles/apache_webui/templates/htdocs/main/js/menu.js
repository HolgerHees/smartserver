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
            if( entries[a]['order'] < entries[b]['order'] ) return -1;
            if( entries[a]['order'] > entries[b]['order'] ) return 1;
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

    ret.addMainGroup = function(mainGroupId,order,title)
    {
        let mainGroup = menuGroups[mainGroupId] = {
            id:mainGroupId,
            uid: mainGroupId,
            order: order,
            title: title,
            subGroups: {},
            _: {
                getId: function(){ return mainGroup['id']; },
                getUId: function(){ return mainGroup['uid']; },
                getType: function(){ return "group"; },
                getTitle: function(){ return mainGroup['title']; },
                getSubGroup: function(subGroupId){ return mainGroup['subGroups'][subGroupId]['_']; },
                //getSubGroups: function(){ return Object.values(mainGroup['subGroups']).map( entry => entry['_'] ); },
                addSubGroup: function(subGroupId,order,title,iconUrl){
                    let subGroup = mainGroup['subGroups'][subGroupId] = {
                        id:subGroupId, uid: mainGroup['uid'] + "-" + subGroupId, order: order, title: title, iconUrl: iconUrl,
                        menuEntries: {},
                        _: {
                            getId: function(){ return subGroup['id']; },
                            getUId: function(){ return subGroup['uid']; },
                            getType: function(){ return "subgroup"; },
                            getTitle: function(){ return subGroup['title']; },
                            getMainGroup: function(){ return mainGroup['_']; },
                            getEntry: function(entryId){ return subGroup['menuEntries'].hasOwnProperty(entryId) ? subGroup['menuEntries'][entryId]['_'] : null; },
                            getEntries: function(){ return filterAllowedEntries(Object.values(subGroup['menuEntries']).map( entry => entry['_'] )); },
                            isSingleEntryGroup: function(){ return Object.values(subGroup['menuEntries']).length == 1; },
                            getMenuEntries: function(){ return filterMenuEntries(subGroup['_']) },
                            addUrl: function(entryId, url, usergroups,order = 0, title = null, info = null, iconUrl = null, newWindow = false){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                let entries = subGroup['menuEntries'];
                                let entry = entries[entryId] = {
                                    id: entryId, uid: subGroup['uid'] + "-" + entryId, order:order,usergroups:usergroups,type:'url',url:url,title:title,info:info,newWindow:newWindow, iconUrl: iconUrl,
                                    _: {
                                        getId: function(){ return entry['id']; },
                                        getUId: function(){ return entry['uid']; },
                                        getType: function(){ return "entry"; },
                                        getOrder: function(){ return entry['order']; },
                                        getUserGroups: function(){ return entry['usergroups']; },
                                        getContentType: function(){ return entry['type']; },
                                        getSubGroup: function(){ return subGroup['_']; },

                                        getTitle: function(){ return entry['title']; },
                                        getInfo: function(){ return entry['info']; },
                                        getIconUrl: function(){ return entry['iconUrl']; },

                                        getNewWindow: function(){ return entry['newWindow']; },
                                        getUrl: function(){ return typeof entry['url'] === 'object' ? entry['url']['callback'](entry['url']['url']) : entry['url']; },

                                        disableLoadingGear: function(){ entry['loadingGearEnabled'] = false},

                                        isLoadingGearEnabled: function(){ return 'loadingGearEnabled' in entry ? entry['loadingGearEnabled'] : true; }
                                    }
                                };
                            },
                            addHtml: function(entryId, html, callback, usergroups, order = 0, title = null, info = null, iconUrl = null){
                                if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                let entries = subGroup['menuEntries'];
                                let entry = entries[entryId] = {
                                    id: entryId, uid: subGroup['uid'] + "-" + entryId, order:order,usergroups:usergroups,type:'html',html:html,callback:callback,title:title,info:info, iconUrl: iconUrl,
                                    _: {
                                        getId: function(){ return entry['id']; },
                                        getUId: function(){ return entry['uid']; },
                                        getType: function(){ return "entry"; },
                                        getOrder: function(){ return entry['order']; },
                                        getUserGroups: function(){ return entry['usergroups']; },
                                        getContentType: function(){ return entry['type']; },
                                        getSubGroup: function(){ return subGroup['_']; },

                                        getTitle: function(){ return entry['title']; },
                                        getInfo: function(){ return entry['info']; },
                                        getIconUrl: function(){ return entry['iconUrl']; },

                                        getHtml: function(){ return entry['html']; },
                                        getCallback: function(){ return entry['callback']; },

                                        isLoadingGearEnabled: function(){ return true; }
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
            
            let match = mainGroup['title'].match(/{i18n_([^}]*)}/);
            if( match !== null ) mainGroup['title'] = mainGroup['title'].replace(match[0],mx.I18N.get(match[1],mainKey));

            for( subKey in mainGroup['subGroups'] )
            {
                let subGroup = mainGroup['subGroups'][subKey];

                subGroup['title'] = processI18N(subGroup['title'],mainKey);

                for( entryKey in subGroup['menuEntries'] )
                {
                    let entry = subGroup['menuEntries'][entryKey];

                    if( entry['title'] ) entry['title'] = processI18N(entry['title'],mainKey+'_'+subKey);
                    if( entry['info'] ) entry['info'] = processI18N(entry['info'],mainKey+'_'+subKey);

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
                    
                    if( entry['usergroups'] && mx.User.memberOf( entry['usergroups'] ) )
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
            menuDiv.querySelector('.header').innerHTML = mainGroup['title'];
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
                button.firstChild.innerHTML = subGroup['iconUrl'] ? '<svg viewBox="0 0 16 16"><use xlink:href="/main/icons/' + subGroup['iconUrl'] + '#icon" /></svg>' : '';
                button.lastChild.innerHTML = subGroup['title'];
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

    function pushEntry(entries, callbacks, currentIndex, entry, html, callback)
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
        if( callback ) callbacks.push(callback);

        return currentIndex
    }
        
    ret.buildContentSubMenu = function(subGroup)
    {
        let entries = [];
        let callbacks = [];

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
                currentIndex = pushEntry(entries, callbacks, currentIndex, entry, entry.getHtml(), entry.getCallback());
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
                        
                        let rect = activeSubmenuElement.getBoundingClientRect();
                        let offsets = mx.Core.getOffsets(activeSubmenuElement);
                        let bottomPos = offsets.top + rect.height;
                        
                        if( bottomPos > mainBottomPos )
                        {
                            mainMenuElement.scrollTo({
                                top: mainMenuElement.scrollTop + ( bottomPos - mainBottomPos ) + 100,
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

    ret.addMainGroup('home', -1, 'Home').addSubGroup('home', -1, 'Home');
    ret.addMainGroup('workspace', 1000, '{i18n_Workspace}');
    ret.addMainGroup('automation', 2000, '{i18n_Automation}');

    let mainGroup = ret.addMainGroup('admin', 3000, '{i18n_Admin}');
    mainGroup.addSubGroup('tools', 200, '{i18n_Tools}', 'core_tools.svg');
    mainGroup.addSubGroup('system', 300, '{i18n_System}', 'core_system.svg');
    mainGroup.addSubGroup('devices', 400, '{i18n_Devices}', 'core_devices.svg');

    return ret;
})( mx.Menu || {} ); 
