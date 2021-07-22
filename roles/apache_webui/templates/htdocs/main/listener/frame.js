frameHandler = (function() {
    if( window.parent != window && window.parent == window.top ){ 
        var head = document.getElementsByTagName("HEAD")[0]
        if( head.hasAttribute("frame-initialized") )
        {
            console.err("Frame already initialized");
        }
        else
        {
            function postMessage(type)
            {
                window.top.postMessage({ type: type, url: document.location.href },'https://' + document.domain); 
            }
          
            head.setAttribute("frame-initialized", "true");

            postMessage("load");

            window.addEventListener("popstate",function(event) { postMessage("popState"); });
            //browser.webNavigation.onHistoryStateUpdated.addListener(function()
            var _pushState = history.pushState; 
            history.pushState = function() { 
                _pushState.apply(this, arguments); 
                postMessage("pushState");
            }; 
            var _replaceState = history.replaceState; 
            history.replaceState = function() { 
                _replaceState.apply(this, arguments); 
                postMessage("replaceState");
            }; 
        }
    } 
})();
