<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#ffffff">
    <link rel="icon" type="image/png" href="/main/img/res/mipmap-mdpi/ic_launcher.png" />
    <link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet"> 
    <link href="main/manifest.json" rel="manifest">
    <link href="main/css/main.css" rel="stylesheet"> 
    <link href="main/css/panel.css" rel="stylesheet"> 

    <script type="text/javascript">var mx = {};</script>
	<script src="main/js/core.js"></script>
	<script src="main/js/swipe.js"></script>
	<script src="main/js/panel.js"></script>

    <script type="text/javascript">
        var alarmIsWorking = true;
        var subMenus = [];
        var menuPanel = false;
        var isPhone = false;
        var imageTitle = "";
        var imageUrl = "";
        var activeMenu = "";
        
        var refreshTimer = [];
        
        var translations = null;

        var readynessCount = 4; //(i18n, background image, background image title & initPage (documentready) )

        var host = location.host;
        var parts = host.split(".");
        var authType = "";
        if( parts.length == 3 )
        {
            var subDomain = parts.shift();
            if( subDomain.indexOf("fa") === 0 ) authType = "fa_";
            else if( subDomain.indexOf("ba") === 0 ) authType = "ba_";
        }
        var domain = parts.join(".");

        function loadBackgroundImage()
        {
            var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
            var src = "/img/potd/today" + ( mx.Core.isSmartphone() ? "Portrait" : "Landscape") + ".jpg?" + id;
            var img = new Image();
            img.onload = function()
            {
                imageUrl = src;
                initContent();
            };
            img.onerror = function()
            {
                initContent();
            };
            img.src = src;
        }

        function loadImageTitle()
        {
            var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
            //openMenu(mx.$('#defaultEntry'),"nextcloud");
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/img/potd/todayTitle.txt?" + id);
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) imageTitle = this.response;
                else alert("was not able to download '/img/potd/todayTitle.txt?'");
                initContent();
            };
            xhr.send();
        }

        function loadI18N()
        {
            var lang = navigator.language || navigator.userLanguage;

            var url = "";
            if( lang.indexOf("de") === 0 ) url = "index.de.json";
            if( url !== "" )
            {
                var xhr = new XMLHttpRequest();
                xhr.open("GET", url, true);
                xhr.onreadystatechange = function() {
                    if (this.readyState != 4) return;

                    if( this.status == 200 ) translations = JSON.parse(this.responseText);
                    else alert("was not able to download '" + url + "'");
                    initContent();
                };
                xhr.send();
            }
            else
            {
                initContent();
            }
        }

        function getI18N(string)
        {
            if( translations )
            {
                if( typeof translations[string] !== "undefined" )
                {
                    return translations[string];
                }
                else
                {
                    console.error("translation key '" + string + "' not found" );
                }
            }
            return string;
        }

        function handleAlarms(data) 
        { 
            var warnCount = 0;
            var errorCount = 0;
            
            for(x in data.alarms) 
            {
                if(!data.alarms.hasOwnProperty(x)) continue;

                var alarm = data.alarms[x];
                if(alarm.status === 'WARNING')
                {
                    warnCount++;
                }
                if(alarm.status === 'CRITICAL')
                {
                    errorCount++;
                }
            }
        
            mx.$$('.alarm.button .badge').forEach(function(element){ element.innerText = warnCount + errorCount });

            var badgeButtons = mx.$$('.alarm.button');
            if( warnCount > 0 )
            {
                badgeButtons.forEach(function(element){ element.classList.add("warn") });
            }
            else
            {
                badgeButtons.forEach(function(element){ element.classList.remove("warn") });
            }
            if( errorCount > 0 )
            {
                badgeButtons.forEach(function(element){ element.classList.add("error") });
            }
            else
            {
                badgeButtons.forEach(function(element){ element.classList.remove("error") });
            }
        }            
       
        function loadAlerts()
        {
            var id = Math.round( Date.now() / 1000 / ( 60 * 60 ) );
            
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "//" + authType + "netdata." + domain + "/api/v1/alarms?active&_=" + id);
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 )
                {
                    if( !alarmIsWorking )
                    {
                        mx.$(".alarm.button").classList.remove("disabled");
                        alarmIsWorking = true;
                    }
                    handleAlarms( JSON.parse(this.response) );
                }
                else if( alarmIsWorking )
                {
                    mx.$(".alarm.button").classList.add("disabled");
                    alarmIsWorking = false;
                }
                window.setTimeout(loadAlerts,5000);
            };
            xhr.send();
        }

        function initAlerts()
        {
            mx.$$('.alarm.button').forEach(function(element){ 
                element.addEventListener("click",function()
                {
                    openUrl(null,null,"//" + authType + "netdata." + domain,false);
                });
            });
            loadAlerts();
        }

        function refreshCamera(container)
        {
            var image = container.querySelector('img');
            var timeSpan = container.querySelector('span.time');
            var nameSpan = container.querySelector('span.name');
            
            var datetime = new Date();
            var h = datetime.getHours();
            var m = datetime.getMinutes();
            var s = datetime.getSeconds();

            var time = ("0" + h).slice(-2) + ':' + ("0" + m).slice(-2) + ':' + ("0" + s).slice(-2);
            timeSpan.innerText = time;
            nameSpan.innerText = image.getAttribute('data-name');
            
            var img = new Image();
            var id = Date.now();
            let src = image.getAttribute('data-src') + '?' + id;
            img.onload = function()
            {
                image.setAttribute('src',src);
            };
            img.onerror = function()
            {
                image.setAttribute('src',src);
            };
            img.src = src;
            
            refreshTimer.push( window.setTimeout(function(){refreshCamera(container)},image.getAttribute('data-interval')) );
        }
        
        function initCamera()
        {
            var containers = mx.$$('.service.camera > div');
            containers.forEach(function(container){

                var timeSpan = document.createElement("span");
                timeSpan.classList.add("time");

                var nameSpan = document.createElement("span");
                nameSpan.classList.add("name");

                container.appendChild(timeSpan);
                container.appendChild(nameSpan);

                refreshCamera(container);
            });
        }
        
        function cleanMenu()
        {
            mx.$$(".service.active").forEach(function(element){ element.classList.remove("active") });
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

        function openMenu(element,key)
        {
            if( activeMenu == key )
            {
              return;
            }
            
            activeMenu = key;
        
            if(refreshTimer.length > 0 )
            {
                for( i = 0; i < refreshTimer.length; i++ )
                {
                    window.clearTimeout(refreshTimer[i]);
                }
                refreshTimer=[];
            }
            
            cleanMenu();
            
            var entries = [];
            var callbacks = [];
            
            //console.log(key);
            //console.log(typeof subMenus[key]);
            //console.log(subMenus[key]);
            
            for(var i = 0; i < subMenus[key].length; i++)
            {
                var entry = subMenus[key][i];

                if( entry[0] == 'html' )
                {
                    entries.push(entry[1]);
                    //entries.push('<div class="service ' + key + '">' + entry[2] + '</div>');
                    //postInit = this[entry[1]];
                }
                else if( entry[0] == 'js' )
                {
                    callbacks.push(this[entry[1]]);
                }
                else
                {
                    entries.push('<div class="service button ' + key + '" onClick="openUrl(event,this,\'' + entry[1] + '\',' + entry[4] + ')"><div>' + entry[2] + '</div><div>' + entry[3] + '</div></div>');
                }
            }
            
            setMenu(entries.join(""),callbacks);
            
            if( element != null ) element.classList.add("active");
        }
             
        function openHome()
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
            if(h >= 18) prefix = getI18N('Good Evening');
            else if(h >  12) prefix = getI18N('Good Afternoon');
            else prefix = getI18N('Good Morning');

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
    echo "            var name = " . json_encode($name) . ";\n";
?>            
            message = '<div class="service home">';
            message += '<div class="time">' + time + '</div>';
            message += '<div class="slogan">' + prefix + ', ' + name + '.</div>';
            message += '<div class="imageTitle">' + imageTitle + '</div>';
            message += '</div>';
            
            if( !isAlreadyActive ) setMenu(message,[]);
            else mx.$('#content #submenu').innerHTML = message;
            
            refreshTimer.push( window.setTimeout(openHome,60000 - (s * 1000)) );
        }
              
        function openUrl(event,element,url,newWindow)
        {
            activeMenu = "";
        
            if( (event && event.ctrlKey) || newWindow )
            {
                var win = window.open(url, '_blank');
                win.focus();
            }
            else
            {
                mx.$$(".service.active").forEach(function(element){ element.classList.remove("active") });
                mx.$("#content #inline").style.display = "none";
                mx.$("#content iframe").style.display = "";
                mx.$("#content iframe").setAttribute('src',url);
            }
        }

        function initMenus()
        {
            subMenus['nextcloud'] = [
                ['url','//' + authType + 'nextcloud.'+domain+'/',getI18N('Documents'),'',false],
                ['url','//' + authType + 'nextcloud.'+domain+'/index.php/apps/news/',getI18N('News'),'',false],
                ['url','//' + authType + 'nextcloud.'+domain+'/index.php/apps/keeweb/',getI18N('Keys'),getI18N('Keeweb'),true]
            ];
            subMenus['openhab'] = [
                ['url','//' + authType + 'openhab.'+domain+'/basicui/app',getI18N('Control'),getI18N('Basic UI'),false],
                ['url','//' + authType + 'openhab.'+domain+'/paperui/index.html',getI18N('Administration'),getI18N('Paper UI'),false],
                ['url','//' + authType + 'openhab.'+domain+'/habpanel/index.html',getI18N('Tablet UI'),getI18N('HabPanel'),false],
                ['url','//' + authType + 'openhab.'+domain+'/habot',getI18N('Chatbot'),getI18N('Habot'),false]
            ];
            subMenus['camera'] = [
                ['html','<div class="service camera">'],
                {% for camera in webui_urls.cameras %}
                    ['html','<div><a href="{{camera.clickUrl}}" target="_blank"><img src="/main/img/loading.png" data-name="{{camera.title}}" data-src="{{camera.imageUrl}}" data-interval="{{camera.interval}}"></a></div>'],
                {% endfor %}
                ['html','</div>'],
                ['js','initCamera']
            ];
            subMenus['tools'] = [
                ['url','/grafana/d/server-health/server-health',getI18N('Charts'),getI18N('Grafana'),false],
                ['url','//' + authType + 'kibana.'+domain+'/app/kibana#/dashboard/1431e9e0-1ce7-11ea-8fe5-3b6764e6f175',getI18N('Analytics'),getI18N('Kibana'),false],
//                ['url','/kibana/app/kibana#/dashboard/02e01270-1b34-11ea-9292-eb71d66d1d45',getI18N('Analytics'),getI18N('Kibana'),false],
                ['url','//' + authType + 'netdata.'+domain+'/',getI18N('State'),getI18N('Netdata'),false]
            ];
            subMenus['admin'] = [
                ['url','/mysql/',getI18N('MySQL'),getI18N('phpMyAdmin'),false],
                ['url','//' + authType + 'openhab.'+domain+'/toolbox/web/weatherDetailOverview.php', getI18N('Weatherforcast'),getI18N('Meteo Group'),false]
            ];
            subMenus['devices'] = [
                {% for device in webui_urls.devices %}
                    ['url','{{device.url}}','{{device.title}}','{{device.name}}','{{device.openInNewWindow}}']{{'' if loop.last else ','}}
                {% endfor %}
            ];
        }

        function initContent()
        {
            readynessCount--;
            if( readynessCount > 0 ) return;

            if( imageUrl !== "" )
            {
                mx.$("body").classList.remove("nobackground" );
                mx.$("#background").style.backgroundImage = "url(" + imageUrl + ")";
            }
            else
            {
                mx.$("body").classList.remove("nobackground" );
            }
            mx.$("#background").style.opacity = "1";

            var elements = document.querySelectorAll("*[data-i18n]");
            elements.forEach(function(element)
            {
                var key = element.getAttribute("data-i18n");
                element.innerHTML = getI18N(key);
            });

            initMenus();

            mx.$('#logo').addEventListener("click",openHome);

            if( !activeMenu ) openHome();

            mx.$('#page').style.opacity = "1";
        }

        function initPage()
        {
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
            
            menuPanel = mx.Panel.init(
                {
                    isSwipeable: true,
                    selectors: {
                        menuButtons: ".burger.button",
                        panelContainer: '#menu'
                    },
                }
            );

            mx.$('#menu').addEventListener("beforeOpen",function(){
                mx.$("#side").classList.remove("fullsize");
                if( isPhone ) mx.$("#layer").classList.add("visible");
            });
            mx.$('#menu').addEventListener("beforeClose",function(){
                mx.$("#side").classList.add("fullsize");
                mx.$("#layer").classList.remove("visible");
            });

            mx.$("#layer").addEventListener("click",function()
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

            initAlerts();
        }

        loadI18N();
        loadBackgroundImage();
        loadImageTitle();

        if (document.readyState === "complete" || document.readyState === "interactive") 
        {
            initPage();
        }
        else 
        {
            document.addEventListener("DOMContentLoaded", initPage);
        }
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
        <div class="group flexInfo autoWidth">
            <div class="header" data-i18n="NextCloud"></div>
            <div class="service button" id="defaultEntry" onClick="openMenu(this,'nextcloud')"><div data-i18n="NextCloud"></div><div></div></div>
        </div>
        <div class="group">
            <div class="header" data-i18n="Automation"></div>
            <div class="service button" onClick="openMenu(this,'openhab')"><div data-i18n="Openhab"></div><div></div></div>
            <div class="service button" onClick="openMenu(this,'camera')"><div data-i18n="Cameras"></div><div></div></div>
        </div>
        <div class="group flexInfo">
            <div class="header" data-i18n="Administration"></div>
            <div class="service button" onClick="openMenu(this,'tools')"><div data-i18n="Logs &amp; States"></div><div></div></div>
            <div class="service button" onClick="openMenu(this,'admin')"><div data-i18n="Tools"></div><div></div></div>
            <div class="service button" onClick="openMenu(this,'devices')"><div data-i18n="Devices"></div><div></div></div>
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
