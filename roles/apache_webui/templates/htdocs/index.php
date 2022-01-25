<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#ffffff">
    <link rel="icon" type="image/png" href="/main/img/res/mipmap-mdpi/ic_launcher.png" />
    <link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet"> 
    <link href="main/manifest.json" rel="manifest">

<?php
function getVersion($path,$suffixes)
{
    $files = scandir($path);
    $time = 0;
    foreach ($files as $name)
    {
        if (in_array($name,array(".","..")))
        {
            continue;
        }

        if( in_array( substr($name,strpos($name,'.')), $suffixes ) )
        {
            $_time = filemtime($path.$name);
            if( $_time > $time ) $time = $_time;
        }
    }
    
    return $time;
}
?>
    <link href="ressources?type=css&version=<?php echo getVersion(__DIR__.'/main/css/',['.css']); ?>" rel="stylesheet">
    
    <script>var mx = { OnScriptReady: [], OnDocReady: [], Translations: [], User: { 'name': '', 'groups': [], 'memberOf': function(usergroups){ if( typeof usergroups == 'string' ) { usergroups = [usergroups]; }; return usergroups.filter(value => mx.User.groups.includes(value)).length > 0; }  } };</script>
    
    <script src="ressources?type=js&version=<?php echo getVersion(__DIR__.'/main/js/',['.js']); ?>"></script>
    
    <script>
<?php
        $name = $_SERVER['REMOTE_USERNAME'];
        $groups = [];
        $handle = fopen("./secret/.htdata", "r");
        if ($handle) {
            while (($line = fgets($handle)) !== false) {
                list($_username,$_name,$_groups) = explode(":", $line);
                if( trim($_username) == $name )
                {
                    $name = trim($_name);
                    $groups = explode(",",trim($_groups));
                    break;
                }
            }

            fclose($handle);
        }
        echo "        mx.User.name = " . json_encode($name) . ";\n";
        echo "        mx.User.groups = " . json_encode($groups) . ";\n";
?>

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
                                    getEntry: function(entryId){ return subGroup['menuEntries'][entryId]['_']; },
                                    getEntries: function(){ return Object.values(subGroup['menuEntries']).map( entry => entry['_'] ); },
                                    addUrl: function(entryId,url,usergroups,order,title,info,newWindow,iconUrl){
                                        if( typeof usergroups == 'string' ) usergroups = [usergroups];
                                        var entries = subGroup['menuEntries'];
                                        var entry = entries[entryId] = {
                                            id: entryId, order:order,usergroups:usergroups,type:'url',url:url,title:title,info:info,newWindow:newWindow, iconUrl: iconUrl,
                                            _: {
                                                isEntry: function(){ return true; },
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
    </script>

    <script src="ressources?type=components&version=<?php echo getVersion(__DIR__.'/main/components/',['.js','*.json']); ?>"></script>

    <script>
        var demoMode = document.location.search.indexOf("demo=") !== -1;

        var pageReady = false;
        
        var menuPanel = false;
        var visualisationType = "phone";

        var readynessCount = 3; //(background image (scriptready), background image title (scriptready) & initPage (documentready) )

        mx.Actions = (function( ret ) {
            var sideElement = null;
            var inlineElement = null;
            var iframeElement = null;
            var iframeProgressElement = null;
            
            var iframeLoadingTimer = null;
            
            function iFrameLoadHandler(e)
            {
                try
                {
                    var url = e.target.contentWindow.location.href;
                    if( url == 'about:blank' && history.state && history.state["entryId"] )
                    {
                        console.log(" ADDITIONAL POP");
                        history.back();
                    }
                }
                catch{}
            }
            
            window.addEventListener("message", (event) => {
                if( 'type' in event.data && [ 'load', 'pushState', 'popState', 'replaceState' ].includes(event.data['type']) )
                {
                    var url = event.data['url'];
                    url = url.split(':',2)[1];
                    if( url.indexOf("//" + window.location.host ) == 0 ) url = url.substr(window.location.host.length+2);
                    loadHandler(url,event.data['type']);
                }
                else
                {
                    console.err("Wrong message" );
                }
            });
            
            function loadHandler(url,type)
            {
                /*if( type == 'replaceState' )
                {
                    console.log("SKIP: " + type + " " + url );
                    return;
                }*/
                
                console.log(">>>> IFRAME " + history.length + " " + url + " <<<<");
                console.log(history.state);

                var entry = mx.History.getEntry(url);
                if( entry )
                {
                    if( entry !== mx.History.getActiveNavigation() )
                    {
                        if( entry.isEntry() )
                        {
                            activateMenu(entry.getSubGroup());
                            mx.History.replaceEntry(entry,null);
                        }
                        else
                        {
                            console.err("Should not happen " + entry.getId() );
                        }
                    }
                    else
                    {
                      mx.History.replaceEntry(entry, entry.getUrl() == url ? null : url );
                    }
                    
                    if( iframeElement.style.display != "" )
                    {
                        hideMenu();
                        showIFrame();
                    }
                }
                else
                {
                    console.err("iFrameLoadHandler: MATCHING HISTORY NOT FOUND");
                }
                
            }
            
            function clearIFrameTimer()
            {
                if( iframeLoadingTimer ) 
                {
                    clearTimeout(iframeLoadingTimer);
                    iframeLoadingTimer = null; 
                }
            }
            
            function setIFrameUrl(url)
            {
                if( iframeElement.getAttribute("url") != url )
                {
                    iframeElement.setAttribute('src', url );

                    iframeProgressElement.style.display = "";
                    
                    // is needed to show iframe content in case of a loading error.
                    // happens e.g. on firefox and not accepted self signed certificates for subdomains in the demo instance
                    iframeLoadingTimer = setTimeout(function(){ showIFrame(); },10000);

                    hideMenu();
                }
            }
            
            function showIFrame()
            {
                if( iframeElement.style.display != "" )
                {
                    clearIFrameTimer();

                    iframeProgressElement.style.display = "none";

                    iframeElement.style.display = "";
                    window.setTimeout(function(){ iframeElement.style.opacity = 1; }, 0);
                }
            }
            
            function hideIFrame()
            {
                if( iframeElement.style.display == "" || iframeProgressElement.style.display == "" )
                {
                    clearIFrameTimer();

                    iframeElement.removeAttribute('src');
                    
                    mx.Core.waitForTransitionEnd(iframeElement,function(){ iframeElement.style.display = "none"; },"setSubMenu2");
                    iframeElement.style.opacity = "";
                    
                    iframeProgressElement.style.display = "none";
                }
            }
            
            function isIFrameVisible()
            {
                return iframeElement.style.display == "";
            }
            
            function hideMenu()
            {
                mx.Timer.clean();

                if( inlineElement.style.display == "" )
                {
                    //mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
                    inlineElement.style.display = "none";
                    sideElement.classList.remove("inline");
                    sideElement.classList.add("iframe");
                }
            }

            function showMenu()
            {
                mx.Timer.clean();

                if( inlineElement.style.display != "" )
                {
                    inlineElement.style.display = "";
                    sideElement.classList.add("inline");
                    sideElement.classList.remove("iframe");

                    hideIFrame();
                }
            }
            
            function fadeInMenu(submenu,callbacks)
            {
                submenu.style.transition = "opacity 200ms linear";
                window.setTimeout( function()
                {
                    mx.Core.waitForTransitionEnd(submenu,function()
                    {
                        if( callbacks.length > 0 ) 
                        {
                            callbacks.forEach(function(callback)
                            {
                                callback();
                            });
                        }
                    },"setSubMenu2");
                    submenu.style.opacity = "";
                },0);
            }

            function setMenuEntries(data,callbacks)
            {
                var submenu = mx.$('#content #submenu');

                if( mx.History.getActiveNavigation() == null || mx.History.getActiveNavigation().isEntry() )
                {
                    submenu.style.opacity = "0";
                    submenu.innerHTML = data;
                    fadeInMenu(submenu,callbacks);
                }
                else
                {
                    submenu.style.transition = "opacity 50ms linear";
                    window.setTimeout( function()
                    {
                        mx.Core.waitForTransitionEnd(submenu,function()
                        {
                            submenu.innerHTML = data;
                            fadeInMenu(submenu,callbacks);
                            
                        },"setSubMenu1");
                        submenu.style.opacity = "0";
                    }, 100);
                }
                
                if( visualisationType != "desktop" ) menuPanel.close();
            }        
            
            function activateMenu(subGroup)
            {
                mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
                
                if( subGroup )
                {
                    var element = document.getElementById(subGroup.getMainGroup().getId() + '-' + subGroup.getId());
                    element.classList.add("active");
                }
            }

            ret.openUrl = function(url)
            {
                setIFrameUrl(url);
            }

            ret.openMenuById = function(event,mainGroupId,subGroupId)
            {
                menu = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId);
                mx.Actions.openMenu(menu,event);
            
            };
            ret.openMenu = function(subGroup,event)
            {
                if( mx.History.getActiveNavigation() === subGroup && !isIFrameVisible() ) return;
                
                if( subGroup.getEntries().length == 1 )
                {
                    mx.Actions.openEntryById(event,subGroup.getMainGroup().getId(),subGroup.getId(),subGroup.getEntries()[0].getId())
                    
                    if( visualisationType != "desktop" ) menuPanel.close();
                }
                else
                {
                    showMenu();
                
                    mx.Menu.buildMenu( subGroup, setMenuEntries);

                    activateMenu(subGroup);

                    mx.History.addMenu(subGroup);
                }
            };

            ret.openEntryById = function(event,mainGroupId,subGroupId,entryId)
            {
                var entry = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId).getEntry(entryId);

                if( (event && event.ctrlKey) || entry.getNewWindow() )
                {
                    var win = window.open(entry.getUrl(), '_blank');
                    win.focus();
                }
                else
                {
                    mx.Actions.openEntry(entry,null);
                }
            };
            
            ret.openEntry = function(entry,url)
            {
                mx.History.addEntry( entry, url );

                activateMenu(entry.getSubGroup());

                var new_url = url ? url : entry.getUrl();
                
                //showIFrame();
                
                setIFrameUrl(new_url);
            };

            ret.openHome = function(event)
            {
                var subGroup = mx.Menu.getMainGroup('home').getSubGroup('home');
                
                var isActive = ( mx.History.getActiveNavigation() === subGroup );
                
                if( !isActive )
                {
                    activateMenu(null);
                    
                    showMenu();
                    
                    mx.History.addMenu(subGroup);
                }

                var datetime = new Date();
                var h = datetime.getHours();
                var m = datetime.getMinutes();
                var s = datetime.getSeconds();
                
                if( demoMode ) h = 20;

                var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2);

                var prefix = '';
                if(h >= 18) prefix = mx.I18N.get('Good Evening');
                else if(h >  12) prefix = mx.I18N.get('Good Afternoon');
                else prefix = mx.I18N.get('Good Morning');

                message = '<div class="service home">';
                message += '<div class="time">' + time + '</div>';
                message += '<div class="slogan">' + prefix + ', ' + mx.User.name + '.</div>';
                message += '<div class="imageTitle">' + mx.MainImage.getTitle() + '</div>';
                message += '</div>';

                if( !isActive ) 
                {
                    setMenuEntries(message,[]);
                }
                else 
                {
                    mx.$('#content #submenu').innerHTML = message;
                    if( typeof event != "undefined" && visualisationType != "desktop" ) menuPanel.close();
                }

                mx.Timer.register(mx.Actions.openHome,60000 - (s * 1000));
            };

            ret.init = function()
            {
                sideElement = mx.$("#side");
                
                inlineElement = mx.$("#content #inline");
                
                iframeProgressElement = mx.$("#content #embedProgress");

                iframeElement = mx.$("#content #embed");
                iframeElement.addEventListener('load', iFrameLoadHandler);    
            }

            return ret;
        })( mx.Actions || {} );

        mx.Page = (function( ret ) {
            ret.checkDeeplink = function(ref)
            {
                if( ref ) 
                {
                    var parts = ref.split(/%7C|\|/);
                    var subMenuGroup = mx.Menu.getMainGroup(parts[0]).getSubGroup(parts[1]);
                    if( parts.length > 2 )
                    {
                        var entry = subMenuGroup.getEntry(parts[2]);
                        
                        mx.Actions.openEntry(entry, parts.length > 3 ? decodeURIComponent( parts[3] ) : null );
                    }
                    else
                    {
                        mx.Actions.openMenu(subMenuGroup);
                    }
                }
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
                        showInfo(animated,mx.I18N.get("VPN Offline"));
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
        })( mx.Page || {} );

        function initContent()
        {
            readynessCount--;
            if( readynessCount > 0 || !pageReady ) return;

            if( mx.MainImage.getUrl() !== "" )
            {
                mx.$("#background").style.backgroundImage = "url(" + mx.MainImage.getUrl() + ")";
                mx.$("#background").style.opacity = mx.darkLayout ? "0.7" : "1";
            }
            else
            {
                mx.$("body").classList.add("nobackground" );
            }

            var elements = document.querySelectorAll("*[data-i18n]");
            elements.forEach(function(element)
            {
                var key = element.getAttribute("data-i18n");
                element.innerHTML = mx.I18N.get(key);
            });

            mx.Menu.init();

            mx.$('#logo').addEventListener("click",mx.Actions.openHome);

            mx.Actions.init();

            var ref = mx.Host.getParameter("ref");

            mx.History.init(function(mainGroup,subGroup,entry,url){
                if( subGroup )
                {
                    if( entry ) mx.Actions.openEntry(entry,url);
                    else mx.Actions.openMenu(subGroup);
                }
                else mx.Actions.openHome();
            });

            mx.Page.checkDeeplink(ref);

            if( !mx.History.getActiveNavigation() ) mx.Actions.openHome();

            mx.$('#page').style.opacity = "1";
        }

        function checkVisualisationType()
        {
            if( window.innerWidth < 600 ) visualisationType = "phone";
            else if( window.innerWidth < 1024 ) visualisationType = "tablet";
            else visualisationType = "desktop";
            
            menuPanel.enableBackgroundLayer(visualisationType !== "desktop");

            if( visualisationType !== "desktop" )
            {
                mx.$("#side").classList.add("fullsize");
            }
            
            if( visualisationType === "phone" )
            {
                mx.$('body').classList.add('phone');
                mx.$('body').classList.remove('desktop');
            }
            else
            {
                mx.$('body').classList.remove('phone');
                mx.$('body').classList.add('desktop');
            }
            
            mx.Page.initTheme();
        }       
        
        function initPage()
        {
            mx.Page.initInfoLayer();
        
            mx.Swipe.init();
                        
            menuPanel = mx.Panel.init({
                isSwipeable: true,
                enableBackgroundLayer: false,
                selectors: {
                    menuButtons: ".burger.button",
                    panelContainer: '#menu',
                    backgroundLayer: '#layer',
                }
            });

            mx.$('#menu').addEventListener("beforeOpen",function(){
                if( visualisationType == "desktop" ) mx.$("#side").classList.remove("fullsize");
            });
            mx.$('#menu').addEventListener("beforeClose",function(){
                if( visualisationType == "desktop" ) mx.$("#side").classList.add("fullsize");
            });

            mx.$("#layer").addEventListener("click",function()
            {
                menuPanel.close();
            });

            function isPhoneListener(mql){ 
                checkVisualisationType(); 
            }
            var phoneMql = window.matchMedia('(max-width: 600px)');
            phoneMql.addListener(isPhoneListener);
            isPhoneListener(phoneMql);

            var desktopMql = window.matchMedia('(min-width: 1024px)');
            function checkMenu(mql)
            {
                checkVisualisationType();

                if( visualisationType === "desktop" ) 
                {
                    mx.$("#side").classList.remove("fullsize");
                    menuPanel.open();
                }
                else 
                {
                    menuPanel.close();
                }
            }
            desktopMql.addListener(checkMenu);
            checkMenu(desktopMql);

            pageReady = true;
        
            initContent();

            if( mx.User.memberOf("admin") )
            {
                // defined in netdata.js (/components/)
                mx.Alarms.init('.alarm.button','.alarm.button .badge');
            }
            else
            {
                mx.$(".alarm.button").style.display = 'none';
            }
            
            mx.$(".spacer").innerHTML = document.location.hostname;
        }
        
        mx.OnScriptReady.push( function(){
            var imageUrl = "/img/potd/today" + ( mx.Core.isSmartphone() ? "Portrait" : "Landscape") + ".jpg";
            if( demoMode ) imageUrl = "https://images.pexels.com/photos/814499/pexels-photo-814499.jpeg";
            var titleUrl = "/img/potd/todayTitle.txt";
            mx.MainImage.init(imageUrl,titleUrl,initContent);
        });

        mx.OnDocReady.push( initPage );
	</script>
</head>
<body>
<script>
    mx.Page = (function( ret ) {
        ret.initTheme = function()
        {
            var darkMql = window.matchMedia( ( demoMode ? '' : '(prefers-color-scheme: dark) and ' ) + '(max-width: 600px)');
            if( darkMql.matches )
            {
                document.body.classList.add("dark");
            }
            else
            {
                document.body.classList.remove("dark");
            }
            document.cookie = "theme=" + ( darkMql.matches ? "dark" : "light" ) + "; expires=0; domain=" + document.location.hostname;
        };
        
        return ret;
    })( mx.Page || {} );
    
    mx.Page.initTheme();
</script>
<div id="page" style="opacity:0;transition:opacity 300ms linear;">
    <div id="menu" class="c-panel">
        <div class="group">
            <div id="logo" class="button"></div>
            <div class="spacer"></div>
            <div class="alarm button">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="currentColor" d="M433.884 366.059C411.634 343.809 384 316.118 384 208c0-79.394-57.831-145.269-133.663-157.83A31.845 31.845 0 0 0 256 32c0-17.673-14.327-32-32-32s-32 14.327-32 32c0 6.75 2.095 13.008 5.663 18.17C121.831 62.731 64 128.606 64 208c0 108.118-27.643 135.809-49.893 158.059C-16.042 396.208 5.325 448 48.048 448H160c0 35.346 28.654 64 64 64s64-28.654 64-64h111.943c42.638 0 64.151-51.731 33.941-81.941zM224 472a8 8 0 0 1 0 16c-22.056 0-40-17.944-40-40h16c0 13.234 10.766 24 24 24z"></path></svg><span class="badge">0</span>
            </div>
            <div class="burger button">
                <svg style="fill:white;stroke:white;" transform="scale(1.0)" enable-background="new 0 0 91 91" id="Layer_1" version="1.1" viewBox="0 0 91 91" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g><rect height="3.4" width="39.802" x="27.594" y="31.362"/><rect height="3.4" width="39.802" x="27.594" y="44.962"/><rect height="3.4" width="39.802" x="27.594" y="58.562"/></g></svg>
            </div>
        </div>
        <div class="group" id="menuTemplate" style="display:none">
            <div class="header"></div>
            <div class="service button"><div></div><div></div></div>
        </div>
        <?php
            if( !isset($_SERVER['AUTH_TYPE']) || $_SERVER['AUTH_TYPE'] != "Basic" )
            {
        ?>
        <a class="logout form button" href="/auth/logout/" data-i18n="Logout"></a>
        <?php
            }
        ?>
    </div>
    <div id="side" class="fullsize">
        <div id="header" data-role="header">
            <div class="burger button">
                <svg style="fill:white;stroke:white;" transform="scale(1.0)" enable-background="new 0 0 91 91" id="Layer_1" version="1.1" viewBox="0 0 91 91" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g><rect height="3.4" width="39.802" x="27.594" y="31.362"/><rect height="3.4" width="39.802" x="27.594" y="44.962"/><rect height="3.4" width="39.802" x="27.594" y="58.562"/></g></svg>
            </div>
            <div class="alarm button">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="currentColor" d="M433.884 366.059C411.634 343.809 384 316.118 384 208c0-79.394-57.831-145.269-133.663-157.83A31.845 31.845 0 0 0 256 32c0-17.673-14.327-32-32-32s-32 14.327-32 32c0 6.75 2.095 13.008 5.663 18.17C121.831 62.731 64 128.606 64 208c0 108.118-27.643 135.809-49.893 158.059C-16.042 396.208 5.325 448 48.048 448H160c0 35.346 28.654 64 64 64s64-28.654 64-64h111.943c42.638 0 64.151-51.731 33.941-81.941zM224 472a8 8 0 0 1 0 16c-22.056 0-40-17.944-40-40h16c0 13.234 10.766 24 24 24z"></path></svg><span class="alarms_count_badge badge">0</span>
            </div>
        </div>
        <div id="content" data-role="main">
            <div id="inline">
                <div id="background"></div>
                <div id="submenu"></div>
            </div>
            <iframe id="embed" frameborder="0" style="display:none"></iframe>
            <div id="embedProgress" style="display:none">
                <svg x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve"><use href="#progress" /></svg>
            </div>
        </div>
    </div>
    <div id="layer"></div>
    <div id="info">
        <div>
            <span class="info"></span>
            <span class="hint"></span>
            <span class="progress">
                <svg id="progress" x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve">
                    <path fill="currentColor" d="M73,50c0-12.7-10.3-23-23-23S27,37.3,27,50 M30.9,50c0-10.5,8.5-19.1,19.1-19.1S69.1,39.5,69.1,50">
                        <animateTransform attributeName="transform" attributeType="XML" type="rotate" dur="1s" from="0 50 50" to="360 50 50" repeatCount="indefinite"></animateTransform>
                    </path>
                </svg>
            </span>
        </div>
    </div>
</div>
</body>
</html>
