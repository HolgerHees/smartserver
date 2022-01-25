mx.Autocomplete = (function( ret ) {
    var _options = {
        input: null,
        values: [],
        top_values: [],
        selected_values: [],
        selectors: {
            selectionLayer: null,
        },
        activeIndex: -1,
        rowCount: 0,
        lastTerm: ""
    };
    
    function show(options)
    {
        options.elements.autocompleteLayer.style.display = "block";
        window.setTimeout(function(){ options.elements.autocompleteLayer.style.opacity = 1; }, 0);

        window.addEventListener('click', options.onBlur);
    }
    
    function hide(options)
    {
        mx.Core.waitForTransitionEnd(options.elements.autocompleteLayer, function(){ 
            options.elements.autocompleteLayer.style.display = ""; 
        },"Autocomplete closed");
        options.elements.autocompleteLayer.style.opacity = "";

        window.removeEventListener('click', options.onBlur);
    }
    
    function removeValue(options, element, value)
    { 
        var index = options.selected_values.indexOf(value);
        options.selected_values.splice(index, 1);
        options.elements.selectionLayer.removeChild(element);
        
        buildValues(options);

        mx.Core.triggerEvent(options.elements.autocompleteLayer, "selectionChanged", false );
    }

    function selectValue(options, value, element)
    {
        var elementSelection = document.createElement("div");
        elementSelection.onclick = function(){ removeValue(options,elementSelection,value) };

        var elementValue = document.createElement("div");
        elementValue.className="value";
        elementValue.innerHTML = value;
        elementSelection.appendChild(elementValue);

        var elementClose = document.createElement("div");
        elementClose.className="close";
        elementClose.innerHTML = "";
        elementSelection.appendChild(elementClose);

        options.elements.selectionLayer.appendChild(elementSelection);
        
        options.selected_values.push(value);
        
        options.elements.autocompleteLayer.removeChild(element);

        mx.Core.triggerEvent(options.elements.autocompleteLayer, "selectionChanged", false );
        
        options.elements.selectionLayer.style.display = options.selected_values.length > 0 ? "flex": "";
    }
    
    function buildValue(options,value,cls)
    {
        var element = document.createElement("div");
        element.innerHTML = value;
        element.className = "row" + ( cls ? " " + cls : "") ;
        element.dataset.value = value;
        element.onclick = function()
        {
            selectValue(options, value, element);
        };
        options.elements.autocompleteLayer.appendChild(element);
    }
    
    function buildValues(options)
    {
        var term = options.input.value;
        if( options.lastTerm == term ) return;
        options.lastTerm = term;
        
        var values = options.values.filter(tag => tag.indexOf(term) != -1 && options.selected_values.indexOf(tag) == -1 );
        var top_values = term == "" ? options.top_values.filter(tag => options.values.indexOf(tag) != -1 ) : [];
               
        options.elements.autocompleteLayer.innerHTML = "";
        
        if( term != "" && options.values.indexOf(term) == -1 )
        {
            buildValue(options, term, "term");
            var element = document.createElement("div");
            element.className = "separator";
            options.elements.autocompleteLayer.appendChild(element);
        }
        
        if( top_values.length > 0 )
        {
            top_values.forEach(function(value)
            {
                buildValue(options, value, null);
            });
            var element = document.createElement("div");
            element.className = "separator";
            options.elements.autocompleteLayer.appendChild(element);
        }

        values.forEach(function(value)
        {
            buildValue(options, value, null);
        });

        options.activeIndex = -1;
        options.visibleRows = options.elements.autocompleteLayer.querySelectorAll(".row");

        options.elements.selectionLayer.style.display = options.selected_values.length > 0 ? "flex": "";
    }
    
    function onFocus(event, options)
    {
        show(options);
        buildValues(options);
    }
    
    function onBlur(event, options)
    {
        if( event.target == options.input || event.target.parentNode == null ) return;
        hide(options);
    }
    
    function onKeyUp(event, options)
    {
        //console.log(event.keyCode);
        if( event.keyCode == 38 )
        {
            options.activeIndex -= 1;
            hightlightRow(options);
        }
        else if( event.keyCode == 40 )
        {
            options.activeIndex += 1;
            hightlightRow(options);
        }
        else if( event.keyCode == 13 )
        {
            selectActiveRow(options);
        }
        else 
        {
            buildValues(options);
        }
    }
    
    function selectActiveRow(options)
    {
        var element = options.visibleRows[options.activeIndex];
        var value = element.dataset.value;
        selectValue(options, value, element);
    }
    
    function hightlightRow(options)
    {
        if( options.activeIndex < 0 ) options.activeIndex = 0;
        else if( options.activeIndex >= options.visibleRows.length ) options.activeIndex = options.visibleRows.length - 1;
        
        options.visibleRows.forEach(function(element){ element.classList.remove("active"); });
        options.visibleRows[options.activeIndex].classList.add("active");           
    }
    
    function createAutocomplete(options)
    {
        options.elements.autocompleteLayer = document.createElement("div");
        options.elements.autocompleteLayer.classList.add("autocompleteLayer");
        options.elements.autocompleteLayer.innerHTML = "";
        var positionInfo = options.input.getBoundingClientRect();
        options.elements.autocompleteLayer.style.width = positionInfo.width + "px";
        options.input.parentNode.appendChild(options.elements.autocompleteLayer);
        
        options.onFocus = function(event) { onFocus(event, options); }
        options.input.addEventListener("focus",options.onFocus);
        options.onKeyUp = function(event) { onKeyUp(event, options); }
        options.input.addEventListener("keyup",options.onKeyUp);

        options.onBlur = function(event) { onBlur(event, options); }
    }
    
    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        options = mx.Core.initElements( options, "Autocompletion" );
        
        if( options === null ) return;
             
        createAutocomplete(options);
      
        return {
            getSelectedValue: function()
            {
                return options.selected_values;
            },
            getRootLayer: function()
            {
                return options.elements.autocompleteLayer;
            },
            setTopValues: function(top_values)
            {
                options.top_values = top_values;
                buildValues(options);
            },
            destroy: function()
            {
                //console.log("destroy");
                
                window.removeEventListener('click', options.onBlur);

                options.input.removeEventListener("focus", options.onFocus);
                options.input.removeEventListener("keyup", options.onKeyUp);

                options.elements.autocompleteLayer.remove();
            }
        };
    };

    return ret;
})( mx.Autocomplete || {} );
