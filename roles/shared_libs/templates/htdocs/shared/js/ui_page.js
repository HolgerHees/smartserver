mx.Page = (function( ret ) {
    let visualisationType = "phone";

    if( document.location.search.indexOf("demo=") != -1 )
    {
        if( document.location.search.indexOf("demo=1") != -1 )
        {
            document.cookie = "demo=1; Domain=." + mx.Host.getDomain() + "; Path=/; SameSite=None; Secure";
        }
        else
        {
            document.cookie = "demo=; Domain=." + mx.Host.getDomain() + "; Path=/; SameSite=None; Secure; expires=Thu, 01 Jan 1970 00:00:00 GMT;";
        }
    }

    cookies = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )
    let theme = cookies[ "theme" ];
    let demo = cookies[ "demo" ] != undefined;

    function createRipple(event) {
        const button = event.currentTarget;
        
        if( button.classList.contains("disabled") ) return;
        
        const circle = document.createElement("span");
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        var offsets = mx.Core.getOffsets(button);
        
        circle.style.width = circle.style.height = diameter + "px";
        circle.style.left = ( event.clientX - (offsets.left + radius) ) + "px";
        circle.style.top = ( event.clientY - (offsets.top + radius) ) + "px";
        circle.classList.add("ripple"); 

        // cleanup for fast repeatedly clicks
        const ripple = button.getElementsByClassName("ripple")[0];
        if (ripple) ripple.remove();
           
        button.appendChild(circle);
        
        // autocleanup. Otherwise the ripple effect happens again if an element is displayed "" => "none" => ""
        window.setTimeout(function(){ circle.remove() },800); // => animation is 600ms
    }
    
    function initRipple(elements)
    {
        for (const element of elements) 
        {
            if( element.dataset.ripple ) continue;

            element.dataset.ripple = 1
            element.addEventListener("click", createRipple);
        }
    }

    function deviceListener(callback)
    {
        if( window.innerWidth <= 600 ) visualisationType = "phone";
        else if( window.innerWidth < 1024 ) visualisationType = "tablet";
        else visualisationType = "desktop";
        
        let body = mx.$('body');
        
        if( visualisationType === "phone" )
        {
            body.classList.add('phone');
            body.classList.remove('desktop');
        }
        else
        {
            body.classList.remove('phone');
            body.classList.add('desktop');
        }
        
        if( callback ) callback(visualisationType);
    }

    function initDeviceListener(callback)
    {
        var phoneMql = window.matchMedia('(max-width: 600px)');
        phoneMql.addListener(function(){ deviceListener(callback); });
        var desktopMql = window.matchMedia('(min-width: 1024px)');
        desktopMql.addListener(function(){ deviceListener(callback); });

        deviceListener(callback);
    }
    
    ret.isDemoMode = function()
    {
        return demo == true;
    }

    ret.isDarkTheme = function()
    {
        return theme == "dark";
    }
    
    ret.handleRequestError = function(status,url,callback,timeout)
    {
        try 
        {
            return window.top.mx.State.handleRequestError(status,url,callback, timeout);
        }
        catch
        {
            return window.setTimeout(callback, timeout);
        }
    }
        
    ret.refreshUI = function(rootElement)
    {
        initRipple(rootElement ? mx._$$(".form.button",rootElement) : mx.$$(".form.button"));
        initRipple(rootElement ? mx._$$(".form.button .buttonSelectionSelector",rootElement) : mx.$$(".form.button .buttonSelectionSelector"));
    }
    
    ret.initFrame = function(spacer_cls, title, _theme)
    {
        let body = mx.$('body');
        body.classList.add("inline");
        if( spacer_cls ) body.classList.add(spacer_cls);
        
        if( _theme != undefined ) theme = _theme
        if( theme ) document.body.classList.add(theme);

        initDeviceListener();

        //console.log("init frame");
        if( title ) document.title = title;
    };
    
    ret.initMain = function(callback, _theme)
    {
        if( _theme != undefined ) theme = _theme
        initDeviceListener(callback);
    }
    
    return ret;
})( mx.Page || {} );
