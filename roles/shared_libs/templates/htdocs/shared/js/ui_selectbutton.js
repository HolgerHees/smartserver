mx.Selectbutton = (function( ret ) {
    var _options = {
        values: {},
        class: "",
        selectors: {
            button: null,
        }
    };
    
    function show(event, options)
    {
        event.stopPropagation();

        options.elements.buttonSelectionLayer.style.display = "block";

        // reset
        options.elements.buttonSelectionLayer.childNodes.forEach(function(element)
        {
            element.style.paddingLeft = "";
        });
        options.elements.buttonSelectionLayer.style.width = "";
        options.elements.buttonSelectionLayer.style.boxSizing = "";
        
        // calculate size
        let buttonRect = options.elements.button.getBoundingClientRect();
        let selectionRect = options.elements.buttonSelectionLayer.getBoundingClientRect();
        if( buttonRect.width -2 > selectionRect.width )
        {
            let diff = buttonRect.width - selectionRect.width;
            if( diff > 19 ) diff = 19;
            
            options.elements.buttonSelectionLayer.childNodes.forEach(function(element)
            {
               element.style.paddingLeft = (diff + 5) + "px";
            });
            
            options.elements.buttonSelectionLayer.style.width = buttonRect.width + "px";
            options.elements.buttonSelectionLayer.style.boxSizing = "border-box";

            //selectionRect = options.elements.buttonSelectionLayer.getBoundingClientRect();
            //buttonRect = options.elements.button.getBoundingClientRect();
            //
            //console.log(buttonRect);
            //console.log(selectionRect);
        }
        
        if( selectionRect.bottom > window.innerHeight )
        {
            options.elements.buttonSelectionLayer.style.bottom = ( buttonRect.height + selectionRect.height - 8 ) + "px";
        }
        
        window.setTimeout(function(){ options.elements.buttonSelectionLayer.style.opacity = 1; }, 0);

        options.elements.buttonSelector.classList.add("open");

        window.addEventListener('click', options.onBlur);
    }
    
    function hide(event, options)
    {
        event.stopPropagation();

        mx.Core.waitForTransitionEnd(options.elements.buttonSelectionLayer, function(){ 
            options.elements.buttonSelectionLayer.style.display = ""; 
        },"Autocomplete closed");
        options.elements.buttonSelectionLayer.style.opacity = "";
        
        options.elements.buttonSelector.classList.remove("open");

        window.removeEventListener('click', options.onBlur);
    }
    
    function toggle(event, options)
    {
        if( options.elements.buttonSelectionLayer.style.display )
        {
            hide(event, options);
        }
        else
        {   
            if( options.elements.button.classList.contains("disabled") ) return;
            show(event, options); 
        }
    }
   
    function createSelectbutton(options)
    {
        options.onBlur = function(event) { hide(event, options); }

        options.elements.container = document.createElement("div");
        options.elements.container.classList.add("buttonSelection");
        if( options["class"] ) 
        {
            let cls = Array.isArray(options["class"]) ? options["class"] : [options["class"]];
            cls.forEach(function(value){
                options.elements.container.classList.add(value);
            });
        }
        mx.Core.insertAfter(options.elements.container, options.elements.button );
        options.elements.container.appendChild(options.elements.button);
        
        let text = options.elements.button.innerText;
        options.elements.button.innerText = "";
        
        options.elements.buttonText = document.createElement("div");
        options.elements.buttonText.innerHTML = text;
        //options.elements.buttonText.classList.add("buttonSelectionText");
        options.elements.button.appendChild(options.elements.buttonText);

        options.elements.buttonSelector = document.createElement("div");
        options.elements.buttonSelector.innerHTML = "<span class=\"icon-play\"></span>";
        options.elements.buttonSelector.classList.add("buttonSelectionSelector");
        options.elements.buttonSelector.onclick = function(event){ toggle(event, options); };
        options.elements.button.appendChild(options.elements.buttonSelector);
        
        options.elements.buttonSelectionLayer = document.createElement("div");
        options.elements.buttonSelectionLayer.classList.add("buttonSelectionLayer");
                
        for( let i = 0; i < options.values.length; i++ )
        {
            let value = options.values[i];
            
            let element = document.createElement("div");
            element.innerHTML = value["text"];
            element.onclick = function(event){ hide(event, options); value["onclick"].bind(options.elements.button)(element); };
            options.elements.buttonSelectionLayer.appendChild(element);
        }
        
        options.elements.container.appendChild(options.elements.buttonSelectionLayer);
    }
    
    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        options = mx.Core.initElements( options, "Selectbutton" );
        
        if( options === null ) return;
             
        createSelectbutton(options);
        
        return {
            toggle: function(event)
            {
                toggle(event, options);
            },
            setText: function(text)
            {
                options.elements.buttonText.innerHTML = text;
            }
        };
    };

    return ret;
})( mx.Selectbutton || {} );
