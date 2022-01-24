mx.Dialog = (function( ret ) {
    var _options = {
        width: "auto",
        height: "auto",
        isBackgroundLayerEnabled: true,
        maxBackgroundLayerOpacity: 0.5,
        buttons: [],
        class: "",
        destroy: false
    };

    var activeInstance = null;
    
    function createDialog(options)
    {
        options.elements.dialogLayer = document.createElement("div");
        options.elements.dialogLayer.classList.add("dialogLayer");
        options.elements.dialogLayer.innerHTML = "<div class=\"box\"><div class=\"header\"></div><div class=\"body\"></div><div class=\"actions\"></div></div>";
        document.body.appendChild(options.elements.dialogLayer);
        
        options.elements.contentBox = options.elements.dialogLayer.querySelector(".box");
        if(options.class) options.elements.contentBox.classList.add(options.class);
        options.elements.contentHeader = options.elements.dialogLayer.querySelector(".header");
        options.elements.contentBody = options.elements.dialogLayer.querySelector(".body");
        options.elements.contentActions = options.elements.dialogLayer.querySelector(".actions");

        if(options.title) options.elements.contentHeader.innerHTML = options.title;
        else options.elements.contentHeader.style.display = "none";
        if(options.body) options.elements.contentBody.innerHTML = options.body;
        else options.elements.contentBody.style.display = "none";
        
        for( i in options.buttons )
        {
            let cfg = options.buttons[i];
            var button = document.createElement("div");
            button.classList.add("form");
            button.classList.add("button");
            if( cfg["class"] ) button.classList.add(cfg["class"]);
            button.onclick = function(){ hideDialog(options); if( cfg["callback"] ) cfg["callback"](); };
            button.innerHTML = cfg["text"];
            options.elements.contentActions.appendChild(button);
        }
    }
    
    function showDialog(options)
    {
        options.elements.dialogLayer.style.display = "flex";
        window.setTimeout(function(){ options.elements.dialogLayer.style.backgroundColor = "rgba(0,0,0,0.5)"; }, 0);
    }
    
    function hideDialog(options)
    {
        mx.Core.waitForTransitionEnd(options.elements.dialogLayer, function(){ 
            options.elements.dialogLayer.style.display = ""; 
            if( options.destroy ) options.elements.dialogLayer.remove();
        },"Dialog closed");
        options.elements.dialogLayer.style.backgroundColor = "rgba(0,0,0,0)";
    }

    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        if( options === null ) return;
             
        createDialog(options);
      
        options._.openEventTriggered = false;

        return {
            open: function()
            {
                showDialog(options);
            },
            close: function()
            {
                hideDialog(options);
            },
            getBody: function()
            {
                return options.elements.contentBody;
            }
        };
    };

    return ret;
})( mx.Dialog || {} );
