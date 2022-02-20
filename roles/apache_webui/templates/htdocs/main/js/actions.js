mx.Actions = (function( ret ) {
    var sideElement = null;
    var inlineElement = null;
    var iframeElement = null;
    var progressElement = null;

    var iframeLoadingTimer = null;
    
    var errorElement = null;
    var activeErrorType = null;

    var demoMode = null;
    var menuPanel = null;
    var visualisationType = null;
    
    var titleUrl = null;
                          
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
                if( entry.getType() == "entry" )
                {
                    mx.Menu.activateMenu(entry.getSubGroup());
                    mx.History.replaceEntry(entry,null);
                }
                else
                {
                    console.error("Should not happen " + entry.getId() );
                }
            }
            else
            {
                if( entry.getType() == "entry" )
                {
                    mx.History.replaceEntry(entry, (entry.getContentType() == "url" && entry.getUrl() == url) ? null : url );
                }
                else
                {
                    console.error("Should not happen " + entry.getType() );
                }
            }
            
            //showError("loading"); 
            showIFrame();
        }
        else
        {
            console.error("iFrameListenerHandler: MATCHING HISTORY NOT FOUND");
        }
        
    }
    
    function iFrameListenerHandler(event)
    {
        if( 'type' in event.data && [ 'load', 'title', 'pushState', 'popState', 'replaceState' ].includes(event.data['type']) )
        {
            if( event.data['type'] == "title" )
            {
                document.title = event.data["title"];
            }
            else
            {
                var url = event.data['url'];
                url = url.split(':',2)[1];
                if( url.indexOf("//" + window.location.host ) == 0 ) url = url.substr(window.location.host.length+2);
                loadHandler(url,event.data['type']);

                if( titleUrl != event.data['url'] )
                {
                    document.title = event.data["title"];
                }
            }

            titleUrl = event.data['url'];
        }
        else
        {
            console.error("Wrong message" );
        }
        //console.log("iFrameListenerHandler");
    }
    
    function iFrameLoadHandler(e)
    {
        try
        {
            //console.log("iframe loaded");
            var url = e.target.contentWindow.location.href;
            if( url == 'about:blank' && history.state && history.state["entryId"] )
            {
                //debugger;
                console.log("iFrameLoadHandler: ADDITIONAL HISTORY POP");
                //console.log(history);
                history.back();
            }
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
            hideIFrame(true);
            hideError();
            showProgress();
            
            iframeElement.setAttribute('src', url );

            // is needed to show iframe content in case of a loading error.
            // happens e.g. on firefox and not accepted self signed certificates for subdomains in the demo instance
            iframeLoadingTimer = setTimeout(function(){ 
              try
              {
                  let url = iframeElement.contentWindow.location.href;
                  loadHandler(url,"fallback");
              }
              catch {
                  showError("loading"); 
              }
            },10000);
            
            hideMenu();
        }
    }

    function removeIFrameUrl()
    {
        iframeElement.removeAttribute('src');
    }
    
    function showError(errorType, parameter)
    {
        hideIFrame();
        hideMenu();
        hideProgress();

        if( errorElement.style.display != "" || activeErrorType != errorType )
        {
            //console.log("showError");

            activeErrorType = errorType;
            let id = errorType + "Error";
            errorElement.style.display = "";
            mx._$$(":scope > div",errorElement).forEach(function(element)
            {
                element.style.display = element.id == id ? "" : "none";
            });
            
            if( errorType == "notfound" )
            {
                let head = mx._$(":scope > #" + id + " > .url",errorElement);
                head.innerHTML = mx.I18N.get(head.dataset.i18n).fill(parameter);
            }
        }
    }
    
    function hideError()
    {
        if( errorElement.style.display == "" )
        {
            //console.log("hideError");
          
            errorElement.style.display = "none";
        }
    }
    
    function showIFrame()
    {
        hideError();
        hideMenu();
        hideProgress();

        if( iframeElement.style.display != "" )
        {
            //console.log("showIFrame");
          
            clearIFrameTimer();

            iframeElement.style.display = "";
            window.setTimeout(function(){ iframeElement.style.opacity = 1; }, 0);
        }
    }
    
    function hideIFrame(immediately)
    {
        clearIFrameTimer();
            
        if( iframeElement.style.display == "" )
        {
            //console.log("hideIFrame");
          
            if( immediately ) iframeElement.style.display = "none";
            else mx.Core.waitForTransitionEnd(iframeElement,function(){ iframeElement.style.display = "none"; },"hideIFrame");
            iframeElement.style.opacity = "";
        }
        
        //hideProgress();
    }
    
    function showProgress()
    {
        if( progressElement.style.display != "" )
        {
            //console.log("showProgress");

            progressElement.style.display = "";
        }
    }

    function hideProgress()
    {
        if( progressElement.style.display == "" ) 
        {
            //console.log("hideProgress");
          
            progressElement.style.display = "none";
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
            //console.log("hideMenu");

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
            //console.log("showMenu");
            
            inlineElement.style.display = "";
            sideElement.classList.add("inline");
            sideElement.classList.remove("iframe");

        }

        removeIFrameUrl();
        hideIFrame();
        hideError();
        hideProgress();
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

        if( mx.History.getActiveNavigation() == null || mx.History.getActiveNavigation().getType() == "entry" )
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
    }        
    
    ret.showError = function(errorType, parameter)
    {
        showError(errorType, parameter);
    }

    ret.showIFrame = function()
    {
        showIFrame();
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

    ret.openMenuById = function(event,subGroupUId)
    {
        [mainGroupId,subGroupId] = subGroupUId.split("-");
        menu = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId);
        mx.Actions.openMenu(menu,event);
    
    };
    ret.openMenu = function(subGroup,event)
    {       
        let entries = subGroup.getEntries();
        if( entries.length == 1 && entries[0].getContentType() == "url" )
        {
            mx.Actions.openEntryById(event,subGroup.getEntries()[0].getUId())
            
            if( visualisationType != "desktop" ) menuPanel.close();
        }
        else
        {
            if( mx.History.getActiveNavigation() !== subGroup || isIFrameVisible() )
            {
                showMenu();
            
                mx.Menu.buildContentSubMenu( subGroup, setMenuEntries);
                
                mx.History.addMenu(subGroup);
            }

            mx.Menu.activateMenu(subGroup);
            
            if( visualisationType != "desktop" && subGroup.getMenuEntries().length == 0 ) menuPanel.close();
        }

    };

    ret.openEntryById = function(event,entryUId)
    {
        [mainGroupId,subGroupId,entryId] = entryUId.split("-");
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

        mx.Menu.activateMenu(entry);

        var new_url = url ? url : entry.getUrl();
        
        //showIFrame();
        
        setIFrameUrl(new_url);

        if( visualisationType != "desktop" ) menuPanel.close();
    };

    ret.openHome = function(event)
    {
        var subGroup = mx.Menu.getMainGroup('home').getSubGroup('home');
        
        var isActive = ( mx.History.getActiveNavigation() === subGroup );
        
        if( !isActive )
        {
            mx.Menu.activateMenu(null);
            
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
            
            if( visualisationType != "desktop" ) menuPanel.close();
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
        errorElement = mx.$("#content #embedError");
        progressElement = mx.$("#content #embedProgress");

        iframeElement = mx.$("#content #embed");
        iframeElement.addEventListener('load', iFrameLoadHandler);                
        
        window.addEventListener("message", iFrameListenerHandler);
    }

    return ret;
})( mx.Actions || {} ); 
