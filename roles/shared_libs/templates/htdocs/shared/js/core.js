mx.$ = function(selector)
{
    return document.querySelector(selector);
};
mx._$ = function(selector, rootElement)
{
    return rootElement.querySelector(selector);
};
mx.$$ = function(selector)
{
    return document.querySelectorAll(selector);
};
mx._$$ = function(selector, rootElement)
{
    return rootElement.querySelectorAll(selector);
};

mx.Core = (function( ret ) {

    function isIncluded(path,target)
    {
        for( var i=0; i < path.length; i++)
        {
            if( path[i] === target )
            {
                return true;
            }
        }
        return false;
    }

    var mergedObjects = ["selectors","elements","callbacks","classes"];

    function merge(ret,options)
    {
        for (var nextKey in options) {
            // Avoid bugs when hasOwnProperty is shadowed
            if (Object.prototype.hasOwnProperty.call(options, nextKey)) {
                if( mergedObjects.indexOf(nextKey) !== -1 )
                {
                    ret[nextKey] = Object.assign( ret[nextKey] === undefined ? {} : ret[nextKey],options[nextKey]);
                }
                else
                {
                    ret[nextKey] = options[nextKey];
                }
            }
        }

        return ret;
    }

    ret.LEVEL = {
        ERROR: 0,
        WARN: 1,
        INFO: 2
    };

    ret.log = function(level,message,element)
    {
        switch( level )
        {
            case mx.Core.LEVEL.ERROR:
            case mx.Core.LEVEL.WARN:
                if( typeof element !== "undefined" ) console.error(message,element);
                else console.error(message);
                break;
            case mx.Core.LEVEL.INFO:
                if( typeof element !== "undefined" ) console.log(message,element);
                else console.log(message);
                break;
        }
    };

    /*
     * Returns an "options" object based on a merge of the default and user provided values
     * Additionally it creates empty containers for
     *    - "elements" => Container for dom node elements
     *    - "_"        => Container for other variables
     */
    ret.initOptions = function(defaults, options)
    {
        var ret = merge({elements:{},_:{}},defaults);
        if( options !== undefined ) ret = merge(ret,options);
        return ret;
    };

    /*
     * Loops over the "selectors" container and tries to initialize the "elements" container
     * and shows an error for not found elements if they are not mentioned in the "selectorsConfig['isOptional']"
     * - Fills "elements"
     * - Using "selectors", "selectorsConfig['asList']" and "selectorsConfig['isOptional']"
     */
    ret.initElements = function(options,source,identifier)
    {
        var hasError = false;
        var selectorsConfig = options.selectorsConfig !== undefined ? options.selectorsConfig : {};

        for( var name in options.selectors )
        {
            // Avoid bugs when hasOwnProperty is shadowed
            if( Object.prototype.hasOwnProperty.call(options.selectors, name) && options.elements[name] === undefined )
            {
                if (selectorsConfig['isManual'] !== undefined && selectorsConfig['isManual'].indexOf(name) !== -1)
                {
                    continue;
                }
                else if (selectorsConfig['asList'] !== undefined && selectorsConfig['asList'].indexOf(name) !== -1)
                {
                    options.elements[name] = options.selectors[name] !== null ? mx.$$(options.selectors[name]) : [];

                    if( options.elements[name].length === 0 && ( selectorsConfig['isOptional'] === undefined || selectorsConfig['isOptional'].indexOf(name) === -1 ) )
                    {
                        mx.Core.log( mx.Core.LEVEL.ERROR, source + ": Can't find elements '" + name + "' by selector '" + options.selectors[name] + "'" );
                        hasError = true;
                    }
                }
                else
                {
                    options.elements[name] = options.selectors[name] !== null ? mx.$(options.selectors[name]) : null;

                    if( options.elements[name] == null && ( selectorsConfig['isOptional'] === undefined || selectorsConfig['isOptional'].indexOf(name) === -1 ) )
                    {
                        mx.Core.log( mx.Core.LEVEL.ERROR, source + ": Can't find element '" + name + "' by selector '" + options.selectors[name] + "'" );
                        hasError = true;
                    }
                }
            }
        }

        if( hasError === true )
        {
            mx.Core.log( mx.Core.LEVEL.ERROR, source + ": " + ( identifier === undefined ? "" : "'" + options.selectors[identifier] + "'" ) + " NOT INITIALIZED !!!");
            return null;
        }


        return options;
    };

    ret.isIEorEdge = function()
    {
        return document.documentMode !== undefined;
    };

    ret.isSmartphone = function()
    {
        return window.innerWidth <= 600 ? mx.Core.isTouchDevice() : false;
    };

    ret.isTouchDevice = function()
    {
        return ("ontouchend" in document);
    };

    ret.isEventTarget = function(event,target)
    {
        var path = event.composedPath();
        return isIncluded(path,target);
    };

    ret.getEvent = function(event)
    {
        return event.touches && event.touches.length > 0 ? event.touches[ 0 ] : event;
    };

    ret.triggerEvent = function(element,name,bubbles,detail)
    {
        var data = {bubbles: bubbles};
        if( detail !== undefined ) data.detail = detail;
        element.dispatchEvent(new CustomEvent(name,data));
    };

    ret.getTransitionDuration = function(element){
        var s = window.getComputedStyle(element).transitionDuration;
        return parseFloat(s) * (s.indexOf('ms') >- 1 ? 1 : 1000);
    };

    ret.waitForTransitionEnd = function(element,callback,source,duration)
    {
        duration = ( duration === undefined ? mx.Core.getTransitionDuration(element) : duration );
        var timeoutHandler = window.setTimeout(function()
        {
            mx.Core.log( source === undefined ? mx.Core.LEVEL.ERROR : mx.Core.LEVEL.INFO, source + ": waitForTransitionEnd Fallback!" );
            handler();
        },duration * 2);

        function handler(e)
        {
            if( !timeoutHandler ) return;
            window.clearTimeout(timeoutHandler);
            timeoutHandler = null;

            // remove finalizeTapEnd handler
            element.removeEventListener("mozTransitionEnd", handler);  // Code for Firefox
            element.removeEventListener("webkitTransitionEnd", handler);  // Code for Safari 3.1 to 6.0
            element.removeEventListener("transitionend", handler);        // Standard syntax

            callback();
        }
        // register finalizeTapEnd handler
        element.addEventListener("mozTransitionEnd", handler);  // Code for Firefox
        element.addEventListener("webkitTransitionEnd", handler);  // Code for Safari 3.1 to 6.0
        element.addEventListener("transitionend", handler);        // Standard syntax
    };

    ret.getOffsets = function(element)
    {
        // only taking care about inline style etc
        // do not use getComputedStyle because this will slow down everything a lot.
        var offsetTop = 0;
        var offsetLeft = 0;
        do
        {
            offsetTop += element.offsetTop ? element.offsetTop : 0;
            offsetLeft += element.offsetLeft ? element.offsetLeft : 0;

            var transform = element.style.transform;
            if(transform.indexOf("translateX") !== -1 )
            {
                var translateX = parseFloat(transform.replace(/[^-\d.]/g, ''));
                offsetLeft += translateX;
            }
            else if(transform.indexOf("translateY") !== -1 )
            {
                var translateY = parseFloat(transform.replace(/[^-\d.]/g, ''));
                offsetTop += translateY;
            }
            else if(transform.indexOf("translate3d") !== -1 )
            {
                transform = getTransform(element);
                offsetLeft += parseInt(transform[0]);
                offsetTop += parseInt(transform[1]);
            }
        }
        while( ( element = element.offsetParent ) !== null );

        return { top: offsetTop, left: offsetLeft };
    };
    
    ret.insertBefore = function(element,ref_element)
    {
        ref_element.parentNode.insertBefore(element, ref_element);
    }
    
    ret.insertAfter = function(element,ref_element)
    {
        if( ref_element.nextSibling )
        {
            ref_element.parentNode.insertBefore(element, ref_element.nextSibling);
        }
        else
        {
            ref_element.parentNode.appendChild(element);
        }
    }
    
    ret.encodeDict = function(params,prefix)
    {
        const query = Object.keys(params).map((key) => {
            const value  = params[key];

            if( params.constructor === Array )
            {
                key = `${prefix}[]`;
            }
            else if( params.constructor === Object )
            {
                key = (prefix ? `${prefix}[${key}]` : key);
            }

            if( typeof value === 'object' && value != null )
            {
                return mx.Core.encodeDict(value, key);
            }
            else if( typeof value === 'boolean' )
            {
                return `${key}=${value ? '1' : '0'}`;
            }
            else if( value === null || typeof value === 'undefined' )
            {
                return `${key}=`;
            }
            else
            {
                return `${key}=${encodeURIComponent(value)}`;
            }
        });

        return [].concat.apply([], query).join('&');
    }

    ret.OnDocReady = function()
    {
        for (var n in mx.OnDocReady) {
            mx.OnDocReady[n].call();
        }

        mx.OnDocReady = {
            push: function(func) {
                func.call();
            }
        };
    };

    return ret;
})( mx.Core || {} );
