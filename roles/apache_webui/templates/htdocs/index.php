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
                entries.sort(function(a,b)
                {
                    if( a['order'] < b['order'] ) return -1;
                    if( a['order'] > b['order'] ) return 1;
                    return 0;
                });

                return entries;
            }

            ret.getMainGroup = function(mainGroupId)
            {
                return menuGroups[mainGroupId]['_'];
            }

            ret.addMainGroup = function(mainGroupId,order,title)
            {
                menuGroups[mainGroupId] = {
                    id:mainGroupId,
                    order: order,
                    title: title,
                    subGroups: {},
                    _: {
                        getSubGroup: function(subGroupId){
                            return menuGroups[mainGroupId]['subGroups'][subGroupId]['_'];
                        },
                        addSubGroup: function(subGroupId,order,title){
                            menuGroups[mainGroupId]['subGroups'][subGroupId] = {
                                id:subGroupId,
                                order: order,
                                title: title,
                                menuEntries: [],
                                _: {
                                    getEntries: function()
                                    {
                                        return menuGroups[mainGroupId]['subGroups'][subGroupId]['menuEntries'];
                                    },
                                    addUrl: function(order,type,url,title,info,newWindow){
                                        menuGroups[mainGroupId]['subGroups'][subGroupId]['menuEntries'].push({order:order,type:type,url:url,title:title,info:info,newWindow:newWindow});
                                    },
                                    addHtml: function(order,html,callback){
                                        menuGroups[mainGroupId]['subGroups'][subGroupId]['menuEntries'].push({order:order,type:'html',html:html,callback:callback});
                                    }
                                }
                            };
                            return menuGroups[mainGroupId]['subGroups'][subGroupId]['_'];
                        }
                    }
                };

                return menuGroups[mainGroupId]['_'];
            }

            ret.buildMenu = function(mainGroupId,subGroupId, callback)
            {
                var entries = [];
                var callbacks = [];

                var menuEntries = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId).getEntries();
                for(var i = 0; i < menuEntries.length; i++)
                {
                    var entry = menuEntries[i];

                    if( entry['type'] == 'html' )
                    {
                        entries.push(entry['html']);
                        callbacks.push(entry['callback']);
                    }
                    else
                    {
                        entries.push('<div class="service button ' + key + '" onClick="mx.Actions.openUrl(event,this,\'' + entry['url'] + '\',' + entry['newWindow'] + ')"><div>' + entry['title'] + '</div><div>' + entry['info'] + '</div></div>');
                    }
                }

                callback(entries.join(""),callbacks);
            }

            ret.init = function()
            {
                for( mainKey in menuGroups )
                {
                    var mainGroup = menuGroups[mainKey];

                    var match = mainGroup['title'].match(/{i18n_([^}]*)}/);
                    if( match !== null ) mainGroup['title'] = mainGroup['title'].replace(match[0],mx.I18N.get(match[1],mainKey));

                    for( subKey in mainGroup['subGroups'] )
                    {
                        var subGroup = mainGroup['subGroups'][subKey];

                        subGroup['title'] = processI18N(subGroup['title'],mainKey);

                        for( var i = 0; i < subGroup['menuEntries'].length; i++ )
                        {
                            var entry = subGroup['menuEntries'][i];

                            if( entry['type'] === 'url' )
                            {
                                entry['title'] = processI18N(entry['title'],mainKey+'_'+subKey);
                                entry['info'] = processI18N(entry['info'],mainKey+'_'+subKey);

                                match = entry['url'].match(/(\/\/)([^\.]*)\.({host})/);
                                if( match !== null ) entry['url'] = entry['url'].replace('//' + match[2] + "." + match[3], "//" + mx.Host.getAuthType() + match[2] + "." + mx.Host.getDomain() );
                            }
                            else
                            {
                                entry['html'] = processI18N(entry['html'],mainKey+'_'+subKey);
                            }
                        }
                    }
                }

                var template = mx.$('#menuTemplate');

                var _menuGroups = sortMenu( Object.values(menuGroups) );
                for( index in _menuGroups )
                {
                    var mainGroup = _menuGroups[index];

                    var menuDiv = template.cloneNode(true);
                    menuDiv.setAttribute('id',mainGroup['id']);
                    menuDiv.querySelector('.header').innerHTML = mainGroup['title'];
                    menuDiv.style.display = "";
                    template.parentNode.appendChild(menuDiv);

                    var buttonTemplate = menuDiv.querySelector('.service.button');
                    menuDiv.removeChild(buttonTemplate);

                    var _subGroups = sortMenu( Object.values(mainGroup['subGroups']) );
                    for( index in _subGroups )
                    {
                        var subGroup = _subGroups[index];

                        var button = buttonTemplate.cloneNode(true);
                        button.setAttribute("onClick","mx.Actions.openMenu(this,'" + mainGroup['id'] + "','" + subGroup['id'] + "');");
                        button.firstChild.innerHTML = subGroup['title'];
                        menuDiv.appendChild(button);

                        subGroup['menuEntries'] = sortMenu( subGroup['menuEntries'] );
                    }
                }
            }

            var mainGroup = ret.addMainGroup('automation', 2000, '{i18n_Automation}');
            mainGroup.addSubGroup('cameras', 900, '{i18n_Cameras}');

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
        var isPhone = false;

        var readynessCount = 3; //(background image (scriptready), background image title (scriptready) & initPage (documentready) )

        mx.Actions = (function( ret ) {
            var activeMenu = "";

            function cleanMenu()
            {
                mx.Timer.clean();

                mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
                mx.$("#content iframe").style.display = "none";
                mx.$("#content iframe").setAttribute('src',"about:blank");
                mx.$("#content #inline").style.display = "";
            }

            function setMenu(data,callbacks)
            {
                var submenu = mx.$('#content #submenu');
                submenu.style.transition = "opacity 50ms linear";
                window.setTimeout( function()
                {
                    mx.Core.waitForTransitionEnd(submenu,function()
                    {
                        submenu.innerHTML = data;
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
                    },"setSubMenu1");
                    submenu.style.opacity = "0";
                },100);

                if( isPhone ) menuPanel.close();
            }        

            ret.openMenu = function(element,mainGroupId,subGroupId)
            {
                key = mainGroupId + '_' + subGroupId;

                if( activeMenu == key ) return;
                activeMenu = key;

                cleanMenu();

                mx.Menu.buildMenu( mainGroupId, subGroupId, setMenu);

                if( element != null ) element.classList.add("active");
            }

            ret.openUrl = function(event,element,url,newWindow)
            {
                mx.Timer.clean();

                activeMenu = "";

                if( (event && event.ctrlKey) || newWindow )
                {
                    var win = window.open(url, '_blank');
                    win.focus();
                }
                else
                {
                    mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
                    mx.$("#content #inline").style.display = "none";
                    mx.$("#content iframe").style.display = "";
                    mx.$("#content iframe").setAttribute('src',url);
                }
            }

            ret.openHome = function()
            {
                let isAlreadyActive = ( activeMenu == "home" );

                if( !isAlreadyActive )
                {
                    activeMenu = "home";
            
                    cleanMenu();
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

                if( !isAlreadyActive ) setMenu(message,[]);
                else mx.$('#content #submenu').innerHTML = message;

                mx.Timer.register(mx.Actions.openHome,60000 - (s * 1000));
            }

            ret.isMenuActive = function()
            {
                return !!activeMenu;
            }

            return ret;
        })( mx.Actions || {} );

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

            if( !mx.Actions.isMenuActive() ) mx.Actions.openHome();

            mx.$('#page').style.opacity = "1";
        }

        function initPage()
        {
            pageReady = true;

            mx.Swipe.init();

            function isPhoneListener(mql){
                isPhone=mql.matches;
                if( isPhone )
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
            var mql = window.matchMedia('(max-width: 600px)');
            mql.addListener(isPhoneListener);
            isPhoneListener(mql);

            menuPanel = mx.Panel.init({
                isSwipeable: true,
                selectors: {
                    menuButtons: ".burger.button",
                    panelContainer: '#menu'
                }
            });

            var menu = mx.$('#menu');
            var layer = mx.$("#layer");

            menu.addEventListener("beforeOpen",function(){
                mx.$("#side").classList.remove("fullsize");
                if( isPhone ) 
                {
                    layer.style.display = "block";
                    layer.style.opacity = "0.4";
                }
            });
            menu.addEventListener("beforeClose",function(){
                mx.$("#side").classList.add("fullsize");
                if( isPhone ) layer.style.opacity = "0.0";
            });
            menu.addEventListener("afterClose",function(){
                if( isPhone ) layer.style.display = "";
            });
            menu.addEventListener("startMove",function(){
                if( !isPhone ) return;
                layer.style.transition = "none";
            });
            menu.addEventListener("endMove",function(){
                if( !isPhone ) return;
                layer.style.transition = "";
            });
            menu.addEventListener("isMoving",function(event){
                if( !isPhone ) return;
                var opacity = Math.round( (event.detail * 0.4 / 100.0) * 100.0 ) / 100.0;
                layer.style.opacity = opacity;
            });

            layer.addEventListener("click",function()
            {
                menuPanel.close();
            });

            if( !isPhone )
            {
                var menuMql = window.matchMedia('(min-width: 800px)');
                function checkMenu()
                {
                    if( menuMql.matches ) menuPanel.open();
                    else menuPanel.close();
                }
                menuMql.addListener(checkMenu);
                checkMenu();
            }

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
            <iframe frameborder="0"></iframe>
        </div>
    </div>
    <div id="layer"></div>
</div>
</body>
</html>
