mx.Page = (function( ret ) {
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
    
    ret.initBody = function()
    {
        var theme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];
        if( theme ) document.body.classList.add(theme);
    };

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
    
    ret.init = function(title)
    {
        if( title && window.parent != window && window.parent == window.top && window.top.document.domain == document.domain ) 
        {
            window.top.postMessage({ type: "title", url: document.location.href, title: "" + title },'https://' + window.top.document.location.host); 
        }
        ret.refreshUI(document);
    };
    
    return ret;
})( mx.Page || {} );
