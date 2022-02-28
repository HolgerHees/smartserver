frameHandler = (function() {
    var head = document.getElementsByTagName("HEAD")[0]
    if( head.hasAttribute("frame-initialized") )
    {
        console.error("Frame already initialized");
    }
    else
    {
        //let title = null;
        head.setAttribute("frame-initialized", "true");
        
        //console.log(document.querySelector('title'));
        //console.log(document.querySelector('title'));
        
        function postMessage(type)
        {
            //console.log("post");
            //title = document.title;
            window.top.postMessage({ type: type, url: window.location.href, title: document.title },'https://' + window.top.location.host); 
        }
        
        function init()
        {
            // enforces an existing title tag
            document.title = document.title;
            
            //console.log("load");
            postMessage("load");
            
            new MutationObserver(function(mutations) {
                //if( title == document.title ) return;
                //console.log("observer change :" + title + ":" + document.title);
                postMessage("title");
            }).observe(
                document.querySelector('title'),
                { subtree: true, characterData: true, childList: true }
            );

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
        
        if (document.readyState === "complete" || document.readyState === "interactive")
        {
            //console.log("already done");
            init();
        }
        else
        {
            document.addEventListener("DOMContentLoaded", init);
        }
    }
})();
