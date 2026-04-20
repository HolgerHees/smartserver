mx.Autocomplete = (function( ret ) {
    var _options = {
        values: [],
        top_values: [],
        show_term: false,
        selected_values: [],
        selectors: {
            input: null,
        },
        activeIndex: -1,
        rowCount: 0,
        lastTerm: null
    };
    
    function show(options)
    {
        options.elements.autocompleteLayer.style.display = "block";
        window.setTimeout(function(){ options.elements.autocompleteLayer.style.opacity = 1; }, 0);

        options.elements.input.addEventListener("keydown",options.onKeyDown);
        window.addEventListener('click', options.onBlur);
    }
    
    function hide(options)
    {
        mx.Core.waitForTransitionEnd(options.elements.autocompleteLayer, function(){ 
            options.elements.autocompleteLayer.style.display = ""; 
        },"Autocomplete closed");
        options.elements.autocompleteLayer.style.opacity = "";

        options.elements.input.removeEventListener("keydown",options.onKeyDown);
        window.removeEventListener('click', options.onBlur);
    }
        
    function addValueToSelection(options,value)
    {
        var elementSelection = document.createElement("div");
        elementSelection.onclick = function(){ removeValue(options,elementSelection,value,true) };

        var elementValue = document.createElement("div");
        elementValue.className="value";
        elementValue.innerHTML = value;
        elementSelection.appendChild(elementValue);

        var elementClose = document.createElement("div");
        elementClose.className="close";
        elementClose.innerHTML = "✖";
        elementSelection.appendChild(elementClose);

        options.elements.selectionLayer.appendChild(elementSelection);
    }
    
    function removeValueFromSelection(options,value)
    {   
        let found = null;
        let elements = options.elements.selectionLayer.childNodes;
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.firstChild.innerHTML == value )
            { 
                found = element;
                break;
            }
        }
        removeValue(options,found,value,false)
    }
    
    function initSelectedValues(options)
    {
        options.selected_values.forEach(function(value){
            addValueToSelection(options,value);
        });

        options.elements.selectionLayer.style.display = options.selected_values.length > 0 ? "flex": "";
        
        //console.log(options.selected_values);
    }
    function removeValue(options, element, value, propagate)
    { 
        var index = options.selected_values.indexOf(value);
        options.selected_values.splice(index, 1);
        options.elements.selectionLayer.removeChild(element);
        
        options.elements.selectionLayer.style.display = options.selected_values.length > 0 ? "flex": "";

        buildValues(options,true);
        
        if( propagate )
        {
            mx.Core.triggerEvent(options.elements.autocompleteLayer, "selectionChanged", false, {"value": value, "added": false } );
        }
    }

    function selectValue(options, value, element)
    {
        options.elements.inputClear.style.display = "hidden";

        options.elements.input.value = "";
        options.elements.input.focus();
        
        addValueToSelection(options,value);
        
        options.selected_values.push(value);
        
        options.elements.selectionLayer.style.display = options.selected_values.length > 0 ? "flex": "";
        
        //options.elements.autocompleteLayer.removeChild(element);
        
        let elements = [... options.elements.autocompleteLayer.childNodes];
        for( let i = 0; i < elements.length; i++ )
        {
            let element = elements[i];
            if( element.dataset.value == value )
            {
                options.elements.autocompleteLayer.removeChild(element);
                if( i + 1 < elements.length && elements[i+1].classList.contains("separator") )
                { 
                    options.elements.autocompleteLayer.removeChild(elements[i+1]);
                    i++;
                }
            }
        }

        mx.Core.triggerEvent(options.elements.autocompleteLayer, "selectionChanged", false, {"value": value, "added": true } );
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
    
    function buildValues(options,force)
    {
        var term = options.elements.input.value.toLowerCase();

        options.elements.inputClear.style.visibility = ( term == "" ? "hidden" : "visible" );

        if( options.lastTerm == term && !force ) return;
        options.lastTerm = term;
        
        var values = options.values.filter(tag => tag.indexOf(term) != -1 && options.selected_values.indexOf(tag) == -1 );
        
        // filter top values out
        // 1. if they not exists in valid values
        // 2. if they are in the first 5 available values
        // 3. if they are selected
        var top_values = term == "" ? options.top_values.filter(tag => options.values.indexOf(tag) > 5 && options.selected_values.indexOf(tag) == -1 ) : [];
        
        options.elements.autocompleteLayer.innerHTML = "";
        
        if( options.show_term && term != "" && options.values.indexOf(term) == -1 )
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
    
    function onClear(event, options)
    {
        options.elements.input.value = "";
        options.elements.input.select();
        buildValues(options,false);
    }

    function onFocus(event, options)
    {
        show(options);
        buildValues(options,false);
    }
    
    function onBlur(event, options)
    {
        if( event.target == options.elements.input || event.target.parentNode == null ) return;
        hide(options);
    }
    
    
    function onKeyUp(event, options)
    {
        //console.log(event.keyCode);
        if( event.keyCode == 38 || event.keyCode == 40 || event.keyCode == 13 || event.keyCode == 27 )
        {
            options.isUpKeyDown = false;
            options.isDownKeyDown = false;
            return;
        }

        buildValues(options,false);
    }
    
    function onKeyDown(event, options)
    {
        //console.log(event.keyCode);
        if( event.keyCode == 38 ) // cursor up
        {
            options.isUpKeyDown = true;
            function longPressedKeyHandler(){ 
                if( !options.isUpKeyDown ) return;
                   
                options.activeIndex -= 1;
                hightlightRow(options,true);
              
                options.longPressedKeyTrigger = window.setTimeout(function(){ longPressedKeyHandler(); },500);
            };
            options.longPressedKeyTrigger = window.setTimeout(function(){ longPressedKeyHandler(); },1000);

            options.activeIndex -= 1;
            hightlightRow(options,true);
        }
        else if( event.keyCode == 40 ) // cursor down
        {
            options.isDownKeyDown = true;
            function longPressedKeyHandler(){ 
                if( !options.isDownKeyDown ) return;

                options.activeIndex += 1;
                hightlightRow(options,false);
              
                options.longPressedKeyTrigger = window.setTimeout(function(){ longPressedKeyHandler(); },500);
            };
            options.longPressedKeyTrigger = window.setTimeout(function(){ longPressedKeyHandler(); },1000);

            options.activeIndex += 1;
            hightlightRow(options,false);
        }
        else if( event.keyCode == 13 ) // enter
        {
            var element = options.visibleRows[options.activeIndex];
            var value = element.dataset.value;
            selectValue(options, value, element);
        }
        else if(event.keyCode == 27 ) // esc
        {
            hide(options);
            options.elements.input.blur();
        }
    }
    
    function hightlightRow(options,is_up)
    {
        if( options.activeIndex < 0 ) options.activeIndex = 0;
        else if( options.activeIndex >= options.visibleRows.length ) options.activeIndex = options.visibleRows.length - 1;
               
        var element = options.visibleRows[options.activeIndex];
        options.visibleRows.forEach(function(element){ element.classList.remove("active"); });
        element.classList.add("active");           

        if( is_up )
        {
            var scrollPos = element.offsetTop;
            if( scrollPos < options.elements.autocompleteLayer.scrollTop )
            {
                options.elements.autocompleteLayer.scrollTop = scrollPos;
            }
        }
        else
        {
            var scrollPos = ( element.offsetTop + element.clientHeight ) - options.elements.autocompleteLayer.clientHeight;
            if( scrollPos > options.elements.autocompleteLayer.scrollTop )
            {
                options.elements.autocompleteLayer.scrollTop = scrollPos;
            }
        }
        
    }
    
    function createAutocomplete(options)
    {
        options.elements.input.autocomplete = "off";
        options.elements.input.classList.add("autoCompletionInput");

        options.elements.inputWrapper = document.createElement("span");
        options.elements.inputWrapper.classList.add("autoCompletionInputWrapper");
        mx.Core.insertAfter(options.elements.inputWrapper,options.elements.input);

        options.elements.inputWrapper.appendChild(options.elements.input);

        options.elements.inputClear = document.createElement("span");
        options.elements.inputClear.classList.add("autoCompletionInputClear");
        options.elements.inputClear.innerHTML = "✖";
        options.elements.inputWrapper.appendChild(options.elements.inputClear);

        options.elements.selectionLayer = document.createElement("div");
        options.elements.selectionLayer.classList.add("autoCompletionSelection");
        mx.Core.insertBefore(options.elements.selectionLayer,options.elements.inputWrapper);

        options.elements.autocompleteLayer = document.createElement("div");
        options.elements.autocompleteLayer.classList.add("autocompleteLayer");
        options.elements.autocompleteLayer.innerHTML = "";
        var positionInfo = options.elements.input.getBoundingClientRect();
        options.elements.autocompleteLayer.style.width = positionInfo.width + "px";
        mx.Core.insertAfter(options.elements.autocompleteLayer,options.elements.inputWrapper);
        
        options.onClear = function(event) { onClear(event, options); }
        options.elements.inputClear.addEventListener("click",options.onClear);

        options.onFocus = function(event) { onFocus(event, options); }
        options.elements.input.addEventListener("focus",options.onFocus);

        options.onKeyUp = function(event) { onKeyUp(event, options); }
        options.elements.input.addEventListener("keyup",options.onKeyUp);

        options.onKeyDown = function(event) { onKeyDown(event, options); }
        options.onBlur = function(event) { onBlur(event, options); }
    }
    
    ret.init = function(options)
    {
        // prepare config options
        options = mx.Core.initOptions(_options,options);

        options = mx.Core.initElements( options, "Autocompletion" );
        
        if( options === null ) return;
             
        createAutocomplete(options);
        
        initSelectedValues(options);
      
        return {
            removeValueFromSelection: function(value)
            {
                removeValueFromSelection(options,value);
            },
            getSelectedValues: function()
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

                options.elements.input.removeEventListener("focus", options.onFocus);
                options.elements.input.removeEventListener("keyup", options.onKeyUp);
                options.elements.input.removeEventListener("keydown", options.onKeyDown);

                options.elements.autocompleteLayer.remove();
            }
        };
    };

    return ret;
})( mx.Autocomplete || {} );
