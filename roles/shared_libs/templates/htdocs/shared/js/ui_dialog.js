mx.Dialog = (function( ret ) {
    var _options = {
        id: null,
        buttons: [],
        class: "",
        destroy: false
    };

    function createDialog(options)
    {
        options.elements.dialogLayer = document.createElement("div");
        options.elements.dialogLayer.classList.add("dialogLayer");
        options.elements.dialogLayer.innerHTML = "<div class=\"box\"><div class=\"header\"></div><div class=\"body\"></div><div class=\"info\"><div></div></div><div class=\"actions\"></div></div>";
        document.body.appendChild(options.elements.dialogLayer);
        
        options.elements.contentBox = options.elements.dialogLayer.querySelector(".box");
        if(options.class) options.elements.contentBox.classList.add(options.class);
        options.elements.contentHeader = options.elements.dialogLayer.querySelector(".header");
        options.elements.contentBody = options.elements.dialogLayer.querySelector(".body");
        options.elements.contentInfoBox = options.elements.dialogLayer.querySelector(".info");
        options.elements.contentInfo = options.elements.dialogLayer.querySelector(".info > div");
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
            if( cfg["class"] ) 
            {
                let cls = Array.isArray(cfg["class"]) ? cfg["class"] : [cfg["class"]];
                cls.forEach(function(value){
                    button.classList.add(value);
                });
            }
            button.onclick = function(){ if( cfg["callback"] ) cfg["callback"](); else hideDialog(options); };
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
            if( options.destroy ) 
            {
                mx.Core.triggerEvent(options.elements.dialogLayer, "destroy", false );
                options.elements.dialogLayer.remove();
            }
        },"Dialog closed");
        options.elements.dialogLayer.style.backgroundColor = "rgba(0,0,0,0)";
    }
    
    function setInfo(options,info)
    {
        if( info != options.elements.contentInfo.innerHTML )
        {
            options.elements.contentInfo.innerHTML = info;
        }

        if( info )
        {
            if( !options.elements.contentInfoBox.style.maxHeight )
            {
                window.setTimeout(function(){ 
                    options.elements.contentInfoBox.style.maxHeight = options.elements.contentInfoBox.scrollHeight + 'px'; 
                }, 0);
            }
        }
        else
        {
            if( options.elements.contentInfoBox.style.maxHeight )
            {
                options.elements.contentInfoBox.style.maxHeight = "";
            }
        }
    }
    
    function setActionDisabled(options,query,disabled)
    {
        let actionElement = options.elements.contentActions.querySelector(query);
        if( disabled )
        {
            actionElement.classList.add("disabled");
        }
        else
        {
            actionElement.classList.remove("disabled");
        }
    }

    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        if( options === null ) return;
             
        createDialog(options);
      
        return {
            open: function()
            {
                showDialog(options);
            },
            close: function()
            {
                hideDialog(options);
            },
            getElement: function(query)
            {
                return options.elements.dialogLayer.querySelector(query);
            },
            getRootElement: function()
            {
                return options.elements.dialogLayer;
            },
            setInfo: function(info )
            {
                setInfo(options,info);
            },
            setActionDisabled: function(query,disabled)
            {
                setActionDisabled(options,query,disabled);
            },
            addEventListener: function(event,callback)
            {
                return options.elements.dialogLayer.addEventListener(event,callback);
            },
            getId: function()
            {
                return options.id;
            }
        };
    };

    return ret;
})( mx.Dialog || {} );
