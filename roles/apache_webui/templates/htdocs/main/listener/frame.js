window.addEventListener("message", function(event)
{
    if( typeof event.data != 'object' || !event.data['type'] || ![ 'css', 'js' ].includes(event.data['type']) ) return;

    switch (event.data['type']) {
        case 'css':
            if( event.data['content'] )
            {
                var node = document.createElement('style');
                node.appendChild(document.createTextNode(event.data['content']));
            }
            else
            {
                var node = document.createElement("link");
                node.href = event.data['src'];
                node.rel = "stylesheet";
                node.type = "text/css";
            }
            document.head.appendChild(node);
            break;
        case 'js':
            var node = document.createElement('script');
            node.setAttribute('type', 'text/javascript');
            node.innerHTML = event.data['content'];
            document.head.appendChild(node);
            break;
    }
});

if( window.parent != window && window.parent == window.top )
{
    window.top.postMessage({ type: 'ping' }, "*");

    frameHandler = (function() {

        var head = document.getElementsByTagName("HEAD")[0]
        if( head.hasAttribute("frame-initialized") )
        {
            console.error("Frame already initialized");
        }
        else
        {
            head.setAttribute("frame-initialized", "true");

            function postMessage(type)
            {
                //console.log("post");
                window.top.postMessage({ type: type, url: window.location.href, title: document.title }, "*");
            }

            function init()
            {
                // enforces an existing title tag
                document.title = document.title;

                //console.log("load");
                postMessage("load");

                new MutationObserver(function(mutations) {
                    postMessage("title");
                }).observe(
                    document.querySelector('title'),
                    { subtree: true, characterData: true, childList: true }
                );

                window.addEventListener("popstate",function(event) { postMessage("popState"); });
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
                init();
            }
            else
            {
                document.addEventListener("DOMContentLoaded", init);
            }
        }
    })();
}
