frameHandler = (function() {
    var head = document.getElementsByTagName("HEAD")[0]
    if( head.hasAttribute("frame-initialized") )
    {
        console.error("Frame already initialized");
    }
    else
    {
        function postMessage(type)
        {
            window.top.postMessage({ type: type, url: window.location.href, title: document.title },'https://' + window.top.location.host); 
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
})();
