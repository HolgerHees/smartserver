<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#ffffff">
    <link rel="icon" type="image/png" href="/main/img/res/mipmap-mdpi/ic_launcher.png" />
    <link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet"> 
    <link href="main/manifest.json" rel="manifest">

    <link href="ressources?type=css" rel="stylesheet">
    
    <script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
    
    <script src="ressources?type=js"></script>
    
	<script type="text/javascript">

    <?php
        $name = $_SERVER['REMOTE_USERNAME'];
        $handle = fopen(".htdata", "r");
        if ($handle) {
            while (($line = fgets($handle)) !== false) {
                list($_username,$_name) = explode(":", $line);
                if( trim($_username) == $name )
                {
                    $name = trim($_name);
                    break;
                }
            }

            fclose($handle);
        }
        echo "        var activeUserName = " . json_encode($name) . ";\n";
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
                return menuGroups[mainGroupId]['_'];
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
                        addSubGroup: function(subGroupId,order,title){
                            var subGroup = mainGroup['subGroups'][subGroupId] = {
                                id:subGroupId,
                                order: order,
                                title: title,
                                menuEntries: {},
                                _: {
                                    isEntry: function(){ return false; },
                                    getId: function(){ return subGroupId; },
                                    getTitle: function(){ return subGroup['title']; },
                                    getMainGroup: function(){ return mainGroup['_']; },
                                    getEntry: function(entryId){ return subGroup['menuEntries'][entryId]['_']; },
                                    getEntries: function(){ return Object.values(subGroup['menuEntries']).map( entry => entry['_'] ); },
                                    addUrl: function(entryId,order,type,url,title,info,newWindow){
                                        var entries = subGroup['menuEntries'];
                                        var entry = entries[entryId] = {
                                            id: entryId, order:order,type:type,url:url,title:title,info:info,newWindow:newWindow,
                                            _: {
                                                isEntry: function(){ return true; },
                                                getId: function(){ return entry['id']; },
                                                //getOrder: function(){ return entry['order']; },
                                                getType: function(){ return entry['type']; },
                                                getSubGroup: function(){ return subGroup['_']; },
                                                getTitle: function(){ return entry['title']; },
                                                getInfo: function(){ return entry['info']; },
                                                getNewWindow: function(){ return entry['newWindow']; },
                                                getUrl: function(){ return entry['url']; }
                                            }
                                        };
                                    },
                                    addHtml: function(entryId,order,html,callback){
                                        var entries = subGroup['menuEntries'];
                                        var entry = entries[entryId] = {
                                            id: entryId, order:order,type:'html',html:html,callback:callback,
                                            _: {
                                                isEntry: function(){ return true; },
                                                getId: function(){ return entry['id']; },
                                                //getOrder: function(){ return entry['order']; },
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
                for(var i = 0; i < menuEntries.length; i++)
                {
                    var entry = menuEntries[i];

                    if( entry.getType() == 'html' )
                    {
                        entries.push(entry.getHtml());
                        callbacks.push(entry.getCallback());
                    }
                    else
                    {
                        entries.push('<div class="service button ' + i + '" onClick="mx.Actions.openEntryById(event,\'' + subGroup.getMainGroup().getId() + '\',\'' + subGroup.getId() + '\',\'' + entry.getId() + '\')"><div>' + entry.getTitle() + '</div><div>' + entry.getInfo() + '</div></div>');
                    }
                }

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
                                entry['title'] = processI18N(entry['title'],mainKey+'_'+subKey);
                                entry['info'] = processI18N(entry['info'],mainKey+'_'+subKey);

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
                    
                    var menuDiv = template.cloneNode(true);
                    menuDiv.setAttribute('id',mainGroup['id']);
                    menuDiv.querySelector('.header').innerHTML = mainGroup['title'];
                    menuDiv.style.display = "";
                    template.parentNode.appendChild(menuDiv);

                    var buttonTemplate = menuDiv.querySelector('.service.button');
                    menuDiv.removeChild(buttonTemplate);

                    var _subGroups = sortMenu( mainGroup['subGroups'] );
                    for( index in _subGroups )
                    {
                        var subGroup = _subGroups[index];

                        var button = buttonTemplate.cloneNode(true);
                        button.setAttribute("id", mainGroup['id'] + '-' + subGroup['id'] );
                        button.setAttribute("onClick","mx.Actions.openMenuById('" + mainGroup['id'] + "','" + subGroup['id'] + "');");
                        button.firstChild.innerHTML = subGroup['title'];
                        menuDiv.appendChild(button);

                        subGroup['menuEntries'] = sortMenu( subGroup['menuEntries'] );
                    }
                }
            };

            ret.addMainGroup('home', -1, 'Home').addSubGroup('home', -1, 'Home');

            var mainGroup = ret.addMainGroup('automation', 2000, '{i18n_Automation}');

            mainGroup = ret.addMainGroup('administration', 3000, '{i18n_Administration}');
            mainGroup.addSubGroup('states', 100, '{i18n_Logs & States}');
            mainGroup.addSubGroup('tools', 200, '{i18n_Tools}');
            mainGroup.addSubGroup('devices', 300, '{i18n_Devices}');

            return ret;
        })( mx.Menu || {} );
    </script>

    <script src="ressources?type=components"></script>

    <script type="text/javascript">
        //var lang = navigator.language || navigator.userLanguage;
        var pageReady = false;
        
        var menuPanel = false;
        var visualisationType = "phone";

        var readynessCount = 3; //(background image (scriptready), background image title (scriptready) & initPage (documentready) )

        mx.Actions = (function( ret ) {
            var activeNavigation = null;
            var activeUrl = null;

            var inlineElement = null;
            var iframeElement = null;
            
            function iFrameLoadHandler(e)
            {
                var url = null;
                try
                {
                    var url = e.target.contentWindow.location.href;
                }
                catch{}
                
                console.log(">>>> IFRAME ") + url + " <<<<";
                console.log(history.state);

                if( url )
                {
                    if( url == 'about:blank' )
                    {
                        // current content entry is still active, so we have to skip the last history back step which is an empty page
                        if( history.state && history.state['entryId'] )
                        {
                            console.log(" ADDITIONAL POP ");
                            history.back();
                        }
                        // this happens if a content page is active and we click on another menu group
                        else
                        {
                            console.log(" SKIPPED POP ");
                        }
                    }
                    else
                    {
                        var entry = mx.Actions.getActiveNavigation();
                        if( entry )
                        {
                            console.log(" ACTIVE ENTRY " + entry.getId() );
                        }
                        mx.Actions.showIFrame(url);
                    }
                }
            }
            
            function setIFrame(url)
            {

                /*var current_url = null;
                try
                {
                    var current_url = iframeElement.contentWindow.location.href;
                    if( current_url != url )
                    {
                        console.log("IFRAME SRC SET " + current_url + ' => ' + url);
                        iframeElement.contentWindow.location.href = url;
                    }
                    else
                    {
                        console.log("IFRAME SRC SKIPPED "+ url );
                    }
                }
                catch
                {
                    iframeElement.setAttribute('src', url );
                }*/         

                iframeElement.setAttribute('src', url );
                //iframeElement.contentWindow.location = url;
            
            }
            
            function showIFrame()
            {
                if( iframeElement.style.display == 'none' )
                {
                    mx.Timer.clean();

                    //mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
                    inlineElement.style.display = "none";

                    iframeElement.style.display = "";
                }
            }

            function cleanMenu()
            {
                mx.Timer.clean();

                inlineElement.style.display = "";
                
                if( iframeElement.style.display == "" )
                {
                    iframeElement.style.display = "none";
                    iframeElement.removeAttribute('src');
                    
                    //iframeElement.contentWindow.location = "about:blank";
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

                if( activeNavigation == null || activeNavigation.isEntry() )
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
                
                var element = document.getElementById(subGroup.getMainGroup().getId() + '-' + subGroup.getId());
                
                element.classList.add("active");
            }

            ret.openMenuById = function(mainGroupId,subGroupId)
            {
                menu = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId);
                mx.Actions.openMenu(menu);
            
            };
            ret.openMenu = function(subGroup)
            {
                if( activeNavigation === subGroup ) return;
                
                cleanMenu();

                mx.Menu.buildMenu( subGroup, setMenuEntries);

                activeNavigation = subGroup
                activeUrl = null;
                  
                activateMenu(subGroup);
                
                mx.History.addMenu(activeNavigation);
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
                    mx.Actions.openEntry(entry);
                }
            };
            
            ret.openEntry = function(entry,url)
            {
                activeNavigation = entry;
                
                activateMenu(entry.getSubGroup());

                var new_url = url ? url : entry.getUrl();
                
                mx.Actions.showIFrame(new_url);
                
                setIFrame(new_url);
                
                mx.History.addEntry( entry, url );
            };

            ret.showIFrame = function(url)
            {
                if( activeUrl != url )
                {
                    activeUrl = url;

                    showIFrame();
                }
            }
            
            ret.openHome = function()
            {
                var subGroup = mx.Menu.getMainGroup('home').getSubGroup('home');
                
                var isActive = ( activeNavigation === subGroup );
                
                if( !isActive )
                {
                    activeNavigation = subGroup;
                    activeUrl = null;

                    cleanMenu();
                    
                    mx.History.addMenu(null);
                }

                var datetime = new Date();
                var h = datetime.getHours();
                var m = datetime.getMinutes();
                var s = datetime.getSeconds();

                var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2);

                var prefix = '';
                if(h >= 18) prefix = mx.I18N.get('Good Evening');
                else if(h >  12) prefix = mx.I18N.get('Good Afternoon');
                else prefix = mx.I18N.get('Good Morning');

                message = '<div class="service home">';
                message += '<div class="time">' + time + '</div>';
                message += '<div class="slogan">' + prefix + ', ' + activeUserName + '.</div>';
                message += '<div class="imageTitle">' + mx.MainImage.getTitle() + '</div>';
                message += '</div>';

                if( !isActive ) setMenuEntries(message,[]);
                else mx.$('#content #submenu').innerHTML = message;

                mx.Timer.register(mx.Actions.openHome,60000 - (s * 1000));
            };

            ret.getActiveNavigation = function()
            {
                return activeNavigation;
            };

            ret.getActiveUrl = function()
            {
                return activeUrl;
            };
            
            ret.init = function()
            {
                inlineElement = mx.$("#content #inline");
                
                iframeElement = mx.$("#content iframe");
                iframeElement.addEventListener('load', iFrameLoadHandler);      
            }

            return ret;
        })( mx.Actions || {} );

        mx.Page = (function( ret ) {
            ret.checkDeeplink = function()
            {
                var ref = mx.Host.getParameter('ref');
                if( ref ) 
                {
                    var parts = ref.split("|");
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
                mx.$("#background").style.opacity = "1";
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

            mx.History.init(function(mainGroup,subGroup,entry,url){
                if( subGroup )
                {
                    if( entry ) mx.Actions.openEntry(entry,url);
                    else mx.Actions.openMenu(subGroup);
                }
                else mx.Actions.openHome();
            });

            mx.Page.checkDeeplink();
            

            if( !mx.Actions.getActiveNavigation() ) mx.Actions.openHome();

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

            // defined in netdata.js (/components/)
            mx.Alarms.init('.alarm.button','.alarm.button .badge');
        }

        mx.OnScriptReady.push( function(){
            var imageUrl = "/img/potd/today" + ( mx.Core.isSmartphone() ? "Portrait" : "Landscape") + ".jpg";
            var titleUrl = "/img/potd/todayTitle.txt";
            mx.MainImage.init(imageUrl,titleUrl,initContent);
        });

        mx.OnDocReady.push( initPage );
	</script>
</head>
<body>
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
        <a class="logout" href="/auth/logout/" data-i18n="Logout"></a>
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
            <iframe frameborder="0" style="display:none"></iframe>
        </div>
    </div>
    <div id="layer"></div>
    <div id="info"><div><span class="info"></span><span class="hint"></span><span class="progress">
    <svg version="1.1" id="L9" x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve">
        <path fill="#fff" d="M73,50c0-12.7-10.3-23-23-23S27,37.3,27,50 M30.9,50c0-10.5,8.5-19.1,19.1-19.1S69.1,39.5,69.1,50">
            <animateTransform attributeName="transform" attributeType="XML" type="rotate" dur="1s" from="0 50 50" to="360 50 50" repeatCount="indefinite"></animateTransform>
        </path>
    </svg>
    </span></div></div>
</div>
</body>
</html>
