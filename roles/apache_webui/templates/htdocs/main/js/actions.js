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
    
    function setTitle(title)
    {
        document.title = title;
    }
    
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
                    mx.Menu.activateMenu(entry);
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
    
    function iFrameMessageEventHandler(event)
    {
        if( 'type' in event.data && [ 'load', 'title', 'pushState', 'popState', 'replaceState' ].includes(event.data['type']) )
        {
            setTitle(event.data["title"]);

            if( event.data['type'] != "title" )
            {
                var url = event.data['url'];
                url = url.split(':',2)[1];
                if( url.indexOf("//" + window.location.host ) == 0 ) url = url.substr(window.location.host.length+2);
                loadHandler(url,event.data['type']);
            }
        }
        else
        {
            console.error("Wrong message" );
        }
        //console.log("iFrameListenerHandler");
    }
    
    function iFrameLoadEventHandler(e)
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
    
    function setIFrameUrl(url, title)
    {
        setTitle( title ? title : "");

        //if( iframeElement.getAttribute("src") != url )
        //{
        hideIFrame(true);
        hideError();
        showProgress();
        
        // is needed to show iframe content in case of a loading error.
        // happens e.g. on firefox and not accepted self signed certificates for subdomains in the demo instance
        iframeLoadingTimer = setTimeout(function(){ 
            try
            {
                let url = iframeElement.contentWindow.location.href;
                if( url != "about:blank" )
                {
                    loadHandler(url,"fallback");
                    return;
                }
            }
            catch (e) {
                //console.log(e);
            }

            showError("loading"); 
        },10000);
        
        iframeElement.setAttribute('src', url );

        hideMenuContent();
        //}
    }

    function removeIFrameUrl()
    {
        iframeElement.removeAttribute('src');
    }
       
    function showIFrame()
    {
        hideError();
        hideMenuContent();
        hideProgress();

        clearIFrameTimer();

        if( iframeElement.style.display != "" )
        {
            //console.log("showIFrame");
          
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
    
    function showError(errorType, parameter)
    {
        setTitle(mx.I18N.get("Error"));

        hideIFrame();
        hideMenuContent();
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
    
    function hideMenuContent()
    {
        mx.Timer.clean();

        if( inlineElement.style.display == "" )
        {
            //console.log("hideMenuContent");

            //mx.$$(".service.active").forEach(function(element){ element.classList.remove("active"); });
            inlineElement.style.display = "none";
            sideElement.classList.remove("inline");
            sideElement.classList.add("iframe");
        }
    }

    function _fadeInMenu(submenu, callbacks)
    {
        submenu.style.transition = "opacity 200ms linear";
        window.setTimeout( function(){
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

    function showMenuContent(content, callbacks, title)
    {
        setTitle(title);
        
        mx.Timer.clean();

        if( inlineElement.style.display != "" )
        {
            //console.log("showMenuContent");
            
            inlineElement.style.display = "";
            sideElement.classList.add("inline");
            sideElement.classList.remove("iframe");

        }

        removeIFrameUrl();
        hideIFrame();
        hideError();
        hideProgress();

        var submenu = mx.$('#content #submenu');

        if( mx.History.getActiveNavigation() == null || mx.History.getActiveNavigation().getType() == "entry" )
        {
            submenu.style.opacity = "0";
            submenu.innerHTML = content;
            _fadeInMenu(submenu, callbacks);
        }
        else
        {
            submenu.style.transition = "opacity 50ms linear";
            window.setTimeout( function()
            {
                mx.Core.waitForTransitionEnd(submenu,function()
                {
                    submenu.innerHTML = content;
                    _fadeInMenu(submenu, callbacks);
                    
                },"setSubMenu1");
                submenu.style.opacity = "0";
            }, 0);
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
        
        setIFrameUrl(new_url, entry.getTitle());

        if( visualisationType != "desktop" ) menuPanel.close();

        inlineElement.classList.add("content");
    };

    ret.openMenuById = function(event,subGroupUId)
    {
        [mainGroupId,subGroupId] = subGroupUId.split("-");
        menu = mx.Menu.getMainGroup(mainGroupId).getSubGroup(subGroupId);
        mx.Actions.openMenu(menu,event);
    
    };
    ret.openMenu = function(subGroup,event)
    {       
        let entries = subGroup.getEntries();
        if( subGroup.isSingleEntryGroup() && entries.length > 0 && entries[0].getContentType() == "url" )
        {
            mx.Actions.openEntryById(event,subGroup.getEntries()[0].getUId())
            
            if( visualisationType != "desktop" ) menuPanel.close();
        }
        else
        {
            if( mx.History.getActiveNavigation() !== subGroup || isIFrameVisible() )
            {
                let data = mx.Menu.buildContentSubMenu( subGroup); // prepare menu content
                
                showMenuContent(data['content'], data['callbacks'], subGroup.getTitle());
            
                mx.History.addMenu(subGroup);
            }

            // should always be called to expand/collapse submenu
            mx.Menu.activateMenu(subGroup);
            
            if( visualisationType != "desktop" && subGroup.getMenuEntries().length == 0 ) menuPanel.close();
            
            inlineElement.classList.add("content");
        }
    };

    ret.openHome = function(event)
    {
        inlineElement.classList.remove("content");

        var subGroup = mx.Menu.getMainGroup('home').getSubGroup('home');
        
        var isActive = ( mx.History.getActiveNavigation() === subGroup );
        
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

        content = '<div class="service home">';
        content += '<div class="time">' + time + '</div>';
        content += '<div class="slogan">' + prefix + ', ' + mx.User.name + '.</div>';
        content += '<div class="bottom"><div class="image"><div class="imageCopyright">' + mx.MainImage.getCopyright() + '</div><div class="imageTitle">' + mx.MainImage.getTitle() + '</div></div></div>';
        content += '</div>';

        if( !isActive || isIFrameVisible() )
        {
            showMenuContent( content, [], subGroup.getTitle());
            
            mx.History.addMenu(subGroup);

            mx.Menu.activateMenu(null); // collapse open submenu
        }
        else
        {
            mx.$('#content #submenu').innerHTML = content;
        }

        if( !isActive ) 
        {           
            if( visualisationType != "desktop" ) menuPanel.close();
        }
        else 
        {
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
        iframeElement.addEventListener('load', iFrameLoadEventHandler);                
        
        window.addEventListener("message", iFrameMessageEventHandler);
    }

    return ret;
})( mx.Actions || {} ); 
