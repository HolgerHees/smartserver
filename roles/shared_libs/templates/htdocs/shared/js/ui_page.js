mx.Page = (function( ret ) {
    let visualisationType = "phone";
    
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
    
    ret.refreshUI = function(rootElement)
    {
        const buttons = rootElement ? mx._$$(".form.button",rootElement) : mx.$$(".form.button");
        for (const button of buttons) 
        {
            if( button.dataset.ripple ) continue;

            button.dataset.ripple = 1
            button.addEventListener("click", createRipple);
        }
    }
    
    ret.initFrame = function(spacer_cls, title)
    {
        let body = mx.$('body');
        body.classList.add("inline");
        if( spacer_cls ) body.classList.add(spacer_cls);
        
        var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
        if( theme ) document.body.classList.add(theme);

        initDeviceListener();

        if( title && window.parent != window && window.parent == window.top && window.top.document.domain == document.domain ) 
        {
            window.top.postMessage({ type: "title", url: document.location.href, title: "" + title },'https://' + window.top.document.location.host); 
        }
    };
    
    ret.initMain = function(callback)
    {
        initDeviceListener(callback);
    }
    
    return ret;
})( mx.Page || {} );
