mx.Actions = (function( ret ) {
    var sideElement = null;
    var inlineElement = null;
    var iframeElement = null;
    var iframeProgressElement = null;
    var iframeErrorElement = null;
    
    var iframeLoadingTimer = null;
    
    var demoMode = null;
    var menuPanel = null;
    var visualisationType = null;
                          
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
                    console.error("Should not happen " + entry.getId() );
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
            console.error("iFrameLoadHandler: MATCHING HISTORY NOT FOUND");
        }
        
    }
    
    function iFrameListenerHandler(event)
    {
        if( 'type' in event.data && [ 'load', 'pushState', 'popState', 'replaceState' ].includes(event.data['type']) )
        {
            var url = event.data['url'];
            url = url.split(':',2)[1];
            if( url.indexOf("//" + window.location.host ) == 0 ) url = url.substr(window.location.host.length+2);
            loadHandler(url,event.data['type']);
        }
        else
        {
            console.error("Wrong message" );
        }
        //console.log("iFrameListenerHandler");
    }
    
    function iFrameLoadHandler(e)
    {
        //console.log("iFrameLoadHandler");
        try
        {
            //console.log("iframe loaded");
            var url = e.target.contentWindow.location.href;
            if( url == 'about:blank' && history.state && history.state["entryId"] )
            {
                console.log(" ADDITIONAL POP");
                history.back();
            }
            //console.log("showIFrame 2");
        }
        catch {}
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
        if( iframeElement.getAttribute("src") != url )
        {
            iframeElement.setAttribute('src', url );

            iframeProgressElement.style.display = "";
            
            // is needed to show iframe content in case of a loading error.
            // happens e.g. on firefox and not accepted self signed certificates for subdomains in the demo instance
            iframeLoadingTimer = setTimeout(function(){ 
              try
              {
                  let url = iframeElement.contentWindow.location.href;
                  loadHandler(url,"fallback");
              }
              catch {
                  showIFrameError(); 
              }
            },10000);
            
            hideMenu();
        }
    }
    
    function hideIFrameError()
    {
        iframeErrorElement.style.display = "none";
        iframeElement.style.display = "";
        window.setTimeout(function(){ iframeElement.style.opacity = 1; }, 0);
    }
    
    function showIFrameError()
    {
        iframeProgressElement.style.display = "none";
        iframeErrorElement.style.display = "";
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

    ret.hideErrorLayer = function()
    {
        hideIFrameError();
    }
    
    ret.openFrameInNewWindow = function()
    {
        var win = window.open(iframeElement.getAttribute("src"), '_blank');
        win.focus();
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
    
    ret.setVisualisationType = function(_visualisationType)
    {
        visualisationType = _visualisationType;
    }

    ret.init = function(_menuPanel, _demoMode)
    {
        demoMode = _demoMode;
        menuPanel = _menuPanel;
        
        sideElement = mx.$("#side");
        
        inlineElement = mx.$("#content #inline");
        
        iframeProgressElement = mx.$("#content #embedProgress");
        iframeErrorElement = mx.$("#content #embedError");

        iframeElement = mx.$("#content #embed");
        iframeElement.addEventListener('load', iFrameLoadHandler);                
        
        window.addEventListener("message", iFrameListenerHandler);
    }

    return ret;
})( mx.Actions || {} ); 
